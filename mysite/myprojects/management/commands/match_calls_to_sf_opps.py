from django.core.management.base import BaseCommand
from myprojects.models import CallRailCall
from datetime import datetime, timedelta
import re
import pandas as pd
from simple_salesforce import Salesforce
from django.utils import timezone
import pytz
from more_itertools import chunked

# Salesforce credentials
username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
sf = Salesforce(username=username, password=password, security_token=security_token)

# Helper to clean phone numbers
def clean_phone(phone_raw):
    if isinstance(phone_raw, float):
        phone_raw = str(phone_raw)[:10]
    else:
        phone_raw = re.sub(r'\D', "", str(phone_raw))
    if phone_raw.startswith("1"):
        phone_raw = phone_raw[-10:]
    return phone_raw if len(phone_raw) == 10 else ""

class Command(BaseCommand):
    def handle(self, *args, **options):
        csv_path = '/Users/colterhill/Documents/Call Data/CallRail Data/Website calls June 2024 - June 2025.csv'
        df = pd.read_csv(csv_path)

        update_sf_opportunity_list = []
        mountain = pytz.timezone('US/Mountain')

        for i, (_, row) in enumerate(df.iterrows()):
            # if i >= 50:
            #     break
            try:
                # Convert call time from Mountain Time to UTC
                naive_call_time = datetime.strptime(row['Start Time'], "%Y-%m-%d %H:%M:%S")
                local_call_time = mountain.localize(naive_call_time)
                call_date_time = local_call_time.astimezone(pytz.UTC)

                number_name = row['Number Name']
                customer_phone = clean_phone(row['Phone Number'])
                call_source = row['Source']
                call_keywords = row['Keywords']
                call_referrer = row['Referrer']
                call_medium = row['Medium']
                call_landing_page = row['Landing Page']
                call_campaign = row['Campaign']
                call_recording = row['Recording Url']

                print(f"\nProcessing call: {customer_phone} at {call_date_time}")

                # Create or update CallRailCall
                call_obj, created = CallRailCall.objects.update_or_create(
                    phone_number=customer_phone,
                    call_date_time=call_date_time,
                    defaults={
                        'number_name': number_name,
                        'call_source': call_source,
                        'call_keywords': call_keywords,
                        'call_referrer': call_referrer,
                        'call_medium': call_medium,
                        'call_landing_page': call_landing_page,
                        'call_campaign': call_campaign,
                        'call_recording': call_recording
                    }
                )

                if created:
                    print("Call saved as new record.")
                else:
                    print("Call already existed; updated record.")

                if not customer_phone:
                    print("Skipped due to missing phone number")
                    continue

                query = f"""
                    SELECT Id, Created_Date_Time__c
                    FROM Opportunity
                    WHERE phone_clean__c = '{customer_phone}' OR mobile_clean__c = '{customer_phone}'
                """
                sf_opp_list = sf.query_all(query)['records']

                print(f"Found {len(sf_opp_list)} opportunities for phone {customer_phone}")

                for opp in sf_opp_list:
                    created_str = opp.get('Created_Date_Time__c')
                    if not created_str:
                        print(f"Opportunity {opp['Id']} has no Created_Date_Time__c")
                        continue

                    try:
                        created_time = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                    except ValueError:
                        print(f"Failed to parse Created_Date_Time__c: {created_str}")
                        continue

                    delta = abs((created_time - call_date_time).total_seconds())
                    print(f"Opportunity {opp['Id']} created at {created_time} (delta {delta} seconds)")

                    if delta <= 3600:
                        sf_opp_dict = {
                            'Id': opp['Id'],
                            'Marketing_Source__c': call_source,
                            'Call_Rail_Number_Name__c': number_name,
                            'Call_Rail_DateTime__c': call_date_time.isoformat(),
                            'Marketing_Campaign__c': call_campaign,
                            'Marketing_Keyword__c': call_keywords,
                            'Call_Rail_Referrer__c': call_referrer,
                            'Marketing_Medium__c': call_medium,
                            'Call_Rail_Landing_Page__c': call_landing_page,
                            'Call_Rail_Recording_URL__c': call_recording,
                        }
                        sf_opp_dict_clean = {k: v for k, v in sf_opp_dict.items() if v is not None and not pd.isna(v)}
                        update_sf_opportunity_list.append(sf_opp_dict_clean)

                        print(f"Matched and queued update for opportunity {opp['Id']}")
                        break

                if not sf_opp_list:
                    print(f"No opportunities found for {customer_phone}")

            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        if update_sf_opportunity_list:
            print(f"\nUpdating {len(update_sf_opportunity_list)} opportunities in Salesforce...")
            for chunk in chunked(update_sf_opportunity_list, 100):
                try:
                    response = sf.bulk.Opportunity.update(chunk, batch_size=100, use_serial=True)
                    print(f"Batch response: {response}")
                except Exception as e:
                    print(f"Batch failed: {e}")
        else:
            print("\nNo opportunities matched for update.")
