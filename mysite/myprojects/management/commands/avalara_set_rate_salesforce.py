import requests
from requests.auth import HTTPBasicAuth
from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce

username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

salesforce = Salesforce(username=username, password=password, security_token=security_token)

# Avalara API credentials
account_number = 2000899182
license_key = "CFF176791390F51C"

# Base URL for the Avalara API (use the production URL when going live)
base_url = "https://rest.avatax.com/api/v2"

# API endpoint for testing (e.g., get tax rates by address)
endpoint = "/taxrates/byaddress"

class Command(BaseCommand):
    def handle(self, *args, **options):

        quote_list_raw = salesforce.query("SELECT Id, QuoteNumber, Total_Price_w_o_Delivery__c, Total_plus_tax__c, Gross_Sales__c, Tax_Amount__c, tax_rate__c, is_delivery__c,  ShippingStreet, ShippingCity, ShippingState, ShippingPostalCode, ShippingCountry FROM Quote WHERE bistrack_order_number_formula__c != NULL AND is_account_base__c = 'YES' AND  ShippingStreet != NULL AND ShippingPostalCode != NULL AND Opp_Close_Date__c > 2024-10-01")
        quote_list = quote_list_raw['records']

        row_count = 0
        for quote in quote_list:
            quote_id = quote['Id']
            quote_number = quote['QuoteNumber']
            gross_sales = quote['Gross_Sales__c']
            sales_without_delivery = quote['Total_Price_w_o_Delivery__c']
            sf_total_plus_tax = quote['Total_plus_tax__c']
            tax_amount = quote['Tax_Amount__c']
            sf_qoute_tax_rate = quote['tax_rate__c']
            is_delivery = quote['is_delivery__c']
            shipping_street = quote['ShippingStreet']
            shipping_city = quote['ShippingCity']
            shipping_state = quote['ShippingState']
            shipping_zipcode = quote['ShippingPostalCode']
            shipping_country = quote['ShippingCountry']
            row_count += 1
            if row_count > 10:
                break
            # print(f"Id: {quote_id}, Number: {quote_number}, Gross Sales: {gross_sales}, SF Tax Rate: {sf_qoute_tax_rate}, SF Total + Tax: {sf_total_plus_tax}")
            # print(f"Street: {shipping_street}, City: {shipping_city}, State: {shipping_state}, ZipCode: {shipping_zipcode}, Country: {shipping_country}")

            # Parameters for the request (e.g., address)
            params = {
                "line1": shipping_street,
                "city": shipping_city,
                "region": shipping_state,
                "postalCode": shipping_zipcode,
                "country": "US"
            }

            # Make the GET request
            response = requests.get(
                base_url + endpoint,
                auth=HTTPBasicAuth(account_number, license_key),
                params=params
            )
            tax_data = response.json()
            total_tax = tax_data['totalRate']
            rates = tax_data['rates']

            # rate_amount = rates['rate']
            # rate_name = rates['name']
            # rate_type = rates['type']

            print(f"SF Quote Number: {quote_number}")
            print(f"Avalara Tax Rate: {total_tax}, SF Tax Rate: {sf_qoute_tax_rate}")
            print(f"Sales: {sales_without_delivery}")
            print(f"SF total + tax: {sf_total_plus_tax}, Avalara total + tax: {(sales_without_delivery * total_tax) + gross_sales}")

            # for rate in rates:
            #     rate_amount = rate['rate']
            #     rate_name = rate['name']
            #     rate_type = rate['type']
            #     print(f"Avalara Tax Rate: {rate_amount}, Name: {rate_name}, Type: {rate_type}, SF tax Rate: {sf_qoute_tax_rate}")

            print(row_count)