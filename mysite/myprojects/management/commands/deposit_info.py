from requests.auth import HTTPBasicAuth
from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
import json
from datetime import datetime, timedelta, date
import pandas as pd

username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

salesforce = Salesforce(username=username, password=password, security_token=security_token)

today_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
yesterday_datetime = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

class Command(BaseCommand):
    def handle(self, *args, **options):
        uploaded_file_name = 'transaction test.csv'

        # Get, open and read file - use file path
        data = pd.read_csv(r'/Users/colterhill/Documents/Deposit Rec/%s' % uploaded_file_name)

        df = pd.DataFrame(data)

        df = df.reset_index()  # make sure indexes pair with number of rows

        row_count = 0
        row_count2 = 0
        payment_data = []
        for row in df.itertuples():
            # row_count += 1

            # if row_count > 20:
            #     continue

            order_id = row.OrderID
            order_number = row.OrderNumber
            order_number_str = str(order_number)
            bistrack_amount = row.Amount
            transaction_datetime = row.TransactionDateTime

            payments_list_raw = salesforce.query(f"SELECT Id, bistrack_order_number__c, Quote_Number__c, CreatedDate, Amount__c FROM Payment__c WHERE CreatedDate > {yesterday_datetime} AND bistrack_order_number__c = '{order_number_str}'")
            payments_list = payments_list_raw['records']

            
            for payment in payments_list:
                
                payment_id = payment['Id']
                bistrack_order_number = payment['bistrack_order_number__c']
                created_datetime = payment['CreatedDate']
                created_date = datetime.strptime(created_datetime, '%Y-%m-%dT%H:%M:%S.%f%z').date()
                # Parse with the timezone offset
                created_datetime_obj = datetime.strptime(created_datetime, '%Y-%m-%dT%H:%M:%S.%f%z')
                # Remove timezone info to make it a naive datetime object
                created_datetime_naive = created_datetime_obj.replace(tzinfo=None)
                amount = payment['Amount__c']
                total_plus_tax = payment['Total_plus_tax__c']
                bt_total_plus_tax = payment['total_tax_in_BT_doesn_t_match_BT__c']
                quote_number = payment['Quote_Number__c']

                # if (amount < (bistrack_amount - 0.10) or amount > (bistrack_amount + 0.10)) and (bistrack_amount > 0):
                #     row_count2 += 1
                #     print(f"BT Num:{bistrack_order_number} SF Quote Num: {quote_number} SF Created Date:{created_datetime_naive} Bistrack Created Date: {transaction_datetime}")
                #     print(f"SF amount: {amount} BT amount: {bistrack_amount}")
                #     print()
                    # payment_data.append({'BT Number': bistrack_order_number, 'SF Quote Number': quote_number, })
                if total_plus_tax != bt_total_plus_tax:
                    print(f"BT Num:{bistrack_order_number} SF Quote Num: {quote_number} SF Created Date:{created_datetime_naive} Bistrack Created Date: {transaction_datetime}")
                    print(f"SF amount: {total_plus_tax} BT amount: {bt_total_plus_tax}")
                    print()
        print(row_count2)