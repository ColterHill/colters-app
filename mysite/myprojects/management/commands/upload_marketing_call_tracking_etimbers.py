from django.core.management.base import BaseCommand
from myprojects.models import MarketingTracker
from datetime import datetime, date, time, timedelta
import math
from simple_salesforce import Salesforce
import pytz
import re
from operator import itemgetter
import requests
import base64
import json
import os
from decimal import Decimal
import pytz
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

        campaign_code = 'eTimbers Calls Jul24'

        uploaded_file_name = 'RingCentral-CallLog-JUL2024.csv'

        # Get, open and read file - use file path
        """
        IMPORTANT update file name and update campaign name below
        """
        data = pd.read_csv(r'/Users/colterhill/Documents/ROI Reports/Call Logs/Jul 2024/%s' % uploaded_file_name)

        df = pd.DataFrame(data)

        df = df.reset_index()  # make sure indexes pair with number of rows

        update_sf_account_list = []
        numbers_checked_list = []
        row_count = 0
        for row in df.itertuples():
            row_count += 1

            # if row_count > 10:
            #     break

            call_date = row._9
            call_source = row.Queue
            customer_phone = clean_phone(row._4)
            sf_account_id = ''
            if customer_phone not in numbers_checked_list:
                numbers_checked_list.append(customer_phone)

                # Try phone clean
                if customer_phone:
                    sf_account_list_raw = salesforce.query_all("SELECT Id FROM Account WHERE is_150_account_base_text__c = 'NO' AND (phone_clean__c = %r OR mobile_clean__c = %r)" % (customer_phone, customer_phone))
                    sf_account_list = sf_account_list_raw['records']
                    if sf_account_list:
                        sf_account_id = sf_account_list[0]['Id']
            if sf_account_id:
                # print here to check before making objects
        #         print(f"ID: {sf_account_id} Call Date: {call_date} Phone#: {customer_phone} Source: {call_source}")
        # print(row_count)

                marketing_tracker, is_new = MarketingTracker.objects.get_or_create(salesforce_account_id=sf_account_id)
                
                if is_new:
                    marketing_tracker.campaign_code = campaign_code
                    marketing_tracker.phone_source = call_source
                    marketing_tracker.save(update_fields=['campaign_code', 'phone_source'])
                    
                    sf_account_dict = {'Id': str(sf_account_id), 'marketing_campaign__c': campaign_code, 'marketing_campaign_phone_source__c': call_source}
                    update_sf_account_list.append(sf_account_dict)


        if len(update_sf_account_list):
            # bulk update salesforce
            resp = salesforce.bulk.Account.update(update_sf_account_list, batch_size=10000, use_serial=True)
            print(resp)
            print(len(update_sf_account_list))
