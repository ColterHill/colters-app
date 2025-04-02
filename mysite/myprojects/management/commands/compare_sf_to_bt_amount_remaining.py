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

last_7_days_filter = date.today()-timedelta(days=7)

today_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
yesterday_datetime = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

class Command(BaseCommand):
    def handle(self, *args, **options):

        quotes_list_raw = salesforce.query(f"SELECT Id, QuoteNumber, bistrack_order_number_formula__c, payment_balance_remaining__c, Total_plus_tax__c, bistrack_amount_with_tax__c, Rep__c, Opp_Close_Date__c, Most_Recent_Payment_Date__c, Most_Recent_Refund_Date__c FROM Quote WHERE Amount_Paid__c > 0 AND Reconciled_in_Accounting__c != True AND Rep__c != 'Colter Hill'")
        quotes_list = quotes_list_raw['records']

        row_count = 0
        row_count2 = 0
        payment_data = []
        for quote in quotes_list:
            sf_quote_id = quote['Id']
            sf_quote_number = quote['QuoteNumber']
            bt_order_number = quote['bistrack_order_number_formula__c']
            sf_amount_remaining = quote['payment_balance_remaining__c']
            sf_total_plus_tax = quote['Total_plus_tax__c']
            bt_total_plus_tax = quote['bistrack_amount_with_tax__c']
            bt_total_plus_tax_float = float(bt_total_plus_tax) if bt_total_plus_tax is not None else 0.0
            
            rep = quote['Rep__c']
            close_date = quote['Opp_Close_Date__c']
            most_recent_sf_refund_date_str = quote['Most_Recent_Refund_Date__c']
            
            year_month_day_format = "%Y-%m-%d"
            most_recent_sf_refund_date = datetime.strptime(most_recent_sf_refund_date_str, year_month_day_format).date() if most_recent_sf_refund_date_str is not None else date.today()-timedelta(days=10)

            most_recent_sf_payment_date_str = quote['Most_Recent_Payment_Date__c']
            most_recent_sf_payment_date = datetime.strptime(most_recent_sf_payment_date_str, year_month_day_format).date() if most_recent_sf_payment_date_str is not None else date.today()-timedelta(days=10)

            # print(f"Quote Number: {sf_quote_number} BT Order Number: {bt_order_number} SF amount remaining: {sf_amount_remaining}")

            # NOW PULL IN DATA FROM A REPORT IN BT
            uploaded_file_name = 'OrdersWithTransactionsInLast7Days.csv'

            # Get, open and read file - use file path
            data = pd.read_csv(r'/Users/colterhill/Documents/Deposit Rec/%s' % uploaded_file_name)

            df = pd.DataFrame(data)

            df = df.reset_index()  # make sure indexes pair with number of rows
            
            for row in df.itertuples():
                biz_order_number = row.OrderNumber
                biz_order_number_str = str(biz_order_number)
                bt_amount_remaining = row.PaymentOutstanding
                recent_payment = row.MostRecentPayment
                recent_payment_date_format = "%m/%d/%Y %H:%M:%S %p"
                recent_payment_date = datetime.strptime(recent_payment, recent_payment_date_format).date()
                
                if bt_order_number == biz_order_number_str and ((sf_amount_remaining - bt_amount_remaining != 0) or (bt_total_plus_tax_float - sf_total_plus_tax != 0)) and (recent_payment_date >= last_7_days_filter or most_recent_sf_refund_date >= last_7_days_filter or most_recent_sf_payment_date >= last_7_days_filter):
                    row_count2 += 1
                    print(f"SF Quote #: {sf_quote_number} Order Number:{biz_order_number_str} Opp Close Date: {close_date} BT Payment date: {recent_payment}  Rep: {rep}")
                    print(f"BT Total + Tax: {bt_total_plus_tax_float} SF Total + Tax: {sf_total_plus_tax}")
                    print(f"SF Balance Remaining: {sf_amount_remaining} BT Balance Remaining: {bt_amount_remaining}")
                    print()

                    payment_data.append({'SF Quote Number': sf_quote_number, 'BT Order Number': bt_order_number, 'Close Date': close_date, 'BT Total': bt_total_plus_tax_float, 'SF Total': sf_total_plus_tax, 'BT Balance': bt_amount_remaining, 'SF Balance': sf_amount_remaining, 'Rep Name': rep, 'SF Quote Link': 'https://rmfp.lightning.force.com/lightning/r/Quote/' + sf_quote_id + '/view'})

        print(row_count2)
        # all_data = pd.DataFrame(payment_data)
        # all_data.to_csv('deposit_discrepency_report.csv', index=False)