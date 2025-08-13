from django.core.management.base import BaseCommand
from myprojects.models import CallRailCall
from datetime import datetime, timedelta
import requests
import pytz
import re
import json
from simple_salesforce import Salesforce
from more_itertools import chunked

# -- Salesforce credentials --
username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
sf = Salesforce(username=username, password=password, security_token=security_token)

# -- CallRail credentials --
API_KEY = "477ac881b043df62d5b0d7104db1fbd2"
ACCOUNT_ID = "227527750"
HEADERS = {
    "Authorization": f"Token token={API_KEY}",
    "Content-Type": "application/json"
}

def clean_phone(phone_raw):
    phone_raw = re.sub(r'\D', "", str(phone_raw))
    if phone_raw.startswith("1"):
        phone_raw = phone_raw[-10:]
    return phone_raw if len(phone_raw) == 10 else ""

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Fetching CallRail call data...")

        fields = ",".join([
            "tracking_phone_number", "source_name", "customer_phone_number",
            "recording_player", "start_time", "keywords", "source",
            "utm_source", "utm_medium", "utm_campaign", "utm_content",
            "landing_page_url", "referring_url", "campaign", "transcription",
            "speaker_percent", "sentiment", "prior_calls", "gclid", "call_summary"
        ])

        all_calls = []
        params = {}
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        initial_url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/calls.json?fields={fields}&relative_pagination=true&per_page=250&start_date={today_str}"

        # initial_url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/calls.json?fields={fields}&relative_pagination=true&per_page=250&start_date=2025-07-10"
        url = initial_url

        while url:
            print(f"Fetching page: {url}")
            response = requests.get(url, headers=HEADERS, params=params if url == initial_url else None)

            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                break

            data = response.json()
            page_calls = data.get("calls", [])
            all_calls.extend(page_calls)
            print(f"✅ Retrieved {len(page_calls)} calls on this page")

            url = data.get("next_page")
            params = None

        print(f"✅ Total calls retrieved: {len(all_calls)}")

        update_sf_opportunity_list = []
        mountain = pytz.timezone('US/Mountain')

        for call in all_calls:
            try:
                duration = call.get('duration', 0)
                if duration is None or duration < 30:
                    print(f"Skipping call with duration: {duration} seconds")
                    continue

                raw_time = call['start_time']
                call_date_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S.%f%z")

                customer_phone = clean_phone(call['customer_phone_number'])
                if not customer_phone:
                    continue

                source_number_name = call['source_name']
                call_recording = call.get('recording_player', "")
                call_keywords = call.get('keywords', "")
                call_source = call.get('source', "")
                call_medium = call.get('utm_medium', "")
                call_referrer = call.get('referring_url', "")
                call_content = call.get('utm_content', "")
                call_landing_page = call.get('landing_page_url', "")
                call_campaign = call.get('campaign', "")
                call_transcription = call.get('transcription', "")
                call_speaker_percent = call.get('speaker_percent', "")
                call_sentiment = call.get('sentiment', "")
                call_prior_calls = call.get('prior_calls', 0)
                call_gclid = call.get('gclid', "")
                call_summary = call.get('call_summary', "")

                CallRailCall.objects.update_or_create(
                    phone_number=customer_phone,
                    call_date_time=call_date_time,
                    defaults={
                        "number_name": source_number_name,
                        "duration": duration,
                        "call_source": call_source,
                        "call_keywords": call_keywords,
                        "call_referrer": call_referrer,
                        "call_medium": call_medium,
                        "call_landing_page": call_landing_page,
                        "call_campaign": call_campaign,
                        "call_utm_content": call_content,
                        "call_recording": call_recording,
                        "call_transcription": call_transcription,
                        "call_agent_speaker_percent": call_speaker_percent.get("agent", 0.0) if isinstance(call_speaker_percent, dict) else 0.0,
                        "call_customer_speaker_percent": call_speaker_percent.get("customer", 0.0) if isinstance(call_speaker_percent, dict) else 0.0,
                        "call_sentiment": call_sentiment,
                        "prior_calls": call_prior_calls,
                        "gclid": call_gclid,
                        "call_summary": call_summary
                    }
                )

                query = f"""
                    SELECT Id, AccountId, Created_Date_Time__c
                    FROM Opportunity
                    WHERE phone_clean__c = '{customer_phone}' OR mobile_clean__c = '{customer_phone}'
                """
                opps = sf.query_all(query).get("records", [])

                for opp in opps:
                    created_str = opp.get("Created_Date_Time__c")
                    if not created_str:
                        continue

                    try:
                        created_time = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                    except ValueError:
                        print(f"⚠️ Failed to parse Created_Date_Time__c: {created_str}")
                        continue

                    call_date_mountain = call_date_time.astimezone(mountain).date()
                    created_date_mountain = created_time.astimezone(mountain).date()

                    if call_date_mountain == created_date_mountain:
                        sf_opp_dict = {
                            'Id': opp['Id'],
                            'Marketing_Source__c': call_source,
                            'Call_Rail_Number_Name__c': source_number_name,
                            'Call_Rail_DateTime__c': call_date_time.isoformat(),
                            'Marketing_Campaign__c': call_campaign,
                            'Marketing_Keyword__c': call_keywords,
                            'Call_Rail_Referrer__c': call_referrer,
                            'Marketing_Medium__c': call_medium,
                            'Marketing_Content__c': call_content,
                            'Call_Rail_Landing_Page__c': call_landing_page,
                            'Call_Rail_Recording_URL__c': call_recording,
                            'Call_Transcription__c': call_transcription,
                            'gclid__c': call_gclid,
                        }

                        # 🆕 New Customer Logic
                        account_id = opp.get("AccountId")
                        is_new_customer = False
                        latest_prior_opp = None

                        if account_id:
                            history_query = f"""
                                SELECT Id, Created_Date_Time__c
                                FROM Opportunity
                                WHERE AccountId = '{account_id}' AND Id != '{opp['Id']}'
                            """
                            prior_opps = sf.query_all(history_query).get("records", [])
                            one_year_ago = call_date_time - timedelta(days=365)

                            prior_dates = []
                            for past_opp in prior_opps:
                                past_created = past_opp.get("Created_Date_Time__c")
                                if not past_created:
                                    continue
                                try:
                                    # Flexible parsing (with or without microseconds)
                                    try:
                                        past_created_dt = datetime.strptime(past_created, "%Y-%m-%dT%H:%M:%S.%f%z")
                                    except ValueError:
                                        past_created_dt = datetime.strptime(past_created, "%Y-%m-%dT%H:%M:%S%z")

                                    if past_created_dt < call_date_time:
                                        prior_dates.append(past_created_dt)
                                except Exception as e:
                                    print(f"⛔ Error parsing prior opp date: {past_created} -> {e}")
                                    continue

                            print(
                                f"📂 Prior opp dates for Account {account_id}: {[dt.isoformat() for dt in prior_dates]}")

                            if not prior_dates:
                                is_new_customer = True
                            else:
                                latest_prior_opp = max(prior_dates)
                                if latest_prior_opp < one_year_ago:
                                    is_new_customer = True

                        # After all prior date checks
                        if is_new_customer:
                            sf_opp_dict["New_Customer__c"] = True
                            print(f"🆕 Marked as New Customer (AccountId: {account_id})")
                        else:
                            sf_opp_dict["New_Customer__c"] = False
                            print(f"👤 Not a New Customer (AccountId: {account_id})")

                        if latest_prior_opp:
                            print(f"📅 Most recent prior opp: {latest_prior_opp.isoformat()}")

                        update_sf_opportunity_list.append({k: v for k, v in sf_opp_dict.items() if v is not None and v != ""})
                        print(f"✅ Matched and queued Opportunity {opp['Id']} for update")
                        break  # Only update one opp per call

            except Exception as e:
                print(f"Error processing call: {e}")
                continue

        if update_sf_opportunity_list:
            print(f"\n🚀 Updating {len(update_sf_opportunity_list)} opportunities in Salesforce...")
            for chunk in chunked(update_sf_opportunity_list, 100):
                try:
                    result = sf.bulk.Opportunity.update(chunk, batch_size=100, use_serial=True)
                    print(f"✅ Batch updated: {result}")
                except Exception as e:
                    print(f"❌ Error in batch update: {e}")
