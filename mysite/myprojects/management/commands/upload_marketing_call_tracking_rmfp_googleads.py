from django.core.management.base import BaseCommand
from myprojects.models import MarketingTracker
from datetime import datetime, date, time, timedelta
import math
from simple_salesforce import Salesforce
from calendar import month_abbr
import re
import pandas as pd


username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

salesforce = Salesforce(username=username, password=password, security_token=security_token)


def clean_phone(phone_raw):
    """
    1) Can't always see float decimal from excel so this strip  the ".0" at end
    2) remove "1" from beginning of phone number if added
    3) If not 10 digit number return " "
    """
    if isinstance(phone_raw, float):
        phone_raw = str(phone_raw)[:10]
    else:
        phone_raw = re.sub(r'\D', "", str(phone_raw))
    if str(phone_raw)[:1] == "1":
        phone_raw = str(phone_raw)[-10:]
    if len(phone_raw) != 10:
        phone_raw = ""
    return phone_raw


class Command(BaseCommand):
    def handle(self, *args, **options):
        uploaded_file_name = 'Google Ads Calls May 1-15 2025.csv'

        data = pd.read_csv(
            r'/Users/colterhill/Documents/ROI Reports/Call Logs/Google Ads/%s' % uploaded_file_name
        )
        df = pd.DataFrame(data)
        df = df.reset_index()

        update_sf_account_list = []
        numbers_checked_list = []
        seen_accounts = set()

        for row in df.itertuples():
            call_date = row._8  # Adjust based on your CSV structure
            number_name = row._5
            customer_phone = clean_phone(row._11)
            sf_account_id = ''

            if not pd.isna(call_date):
                if isinstance(call_date, str):
                    call_date_obj = pd.to_datetime(call_date)
                else:
                    call_date_obj = call_date

                month_str = month_abbr[call_date_obj.month]
                year_short = str(call_date_obj.year)[-2:]  # "25"
                campaign_code = f"Google Ads {month_str}{year_short}"
            else:
                continue  # skip rows with no call date

            if customer_phone and customer_phone not in numbers_checked_list:
                numbers_checked_list.append(customer_phone)

                sf_account_list_raw = salesforce.query_all(
                    "SELECT Id FROM Account WHERE (phone_clean__c = %r OR mobile_clean__c = %r)" %
                    (customer_phone, customer_phone)
                )
                sf_account_list = sf_account_list_raw['records']
                if sf_account_list:
                    sf_account_id = sf_account_list[0]['Id']

            if sf_account_id and (sf_account_id, campaign_code) not in seen_accounts:
                seen_accounts.add((sf_account_id, campaign_code))

                print(f"ID: {sf_account_id} Call Date: {call_date} Phone#: {customer_phone} Source: {number_name}")
                print(campaign_code)
                print()

                marketing_tracker, is_new = MarketingTracker.objects.get_or_create(
                    salesforce_account_id=sf_account_id,
                    campaign_code=campaign_code  # avoid duplicate tracker for same campaign
                )

                if is_new:
                    marketing_tracker.phone_source = number_name
                    marketing_tracker.call_date = call_date_obj
                    marketing_tracker.save(update_fields=['campaign_code', 'phone_source', 'call_date'])

                    sf_account_dict = {
                        'Id': str(sf_account_id),
                        'marketing_campaign__c': campaign_code,
                        'marketing_campaign_phone_source__c': number_name
                    }
                    update_sf_account_list.append(sf_account_dict)

        if update_sf_account_list:
            resp = salesforce.bulk.Account.update(update_sf_account_list, batch_size=10000, use_serial=True)
            print(resp)
            print(f"Updated {len(update_sf_account_list)} accounts")