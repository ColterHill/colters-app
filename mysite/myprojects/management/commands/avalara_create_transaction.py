from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
from datetime import datetime
import requests
import base64
import json
import pytz
import pandas as pd


username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

# Avalara API credentials
account_number = 2000899182
license_key = "CFF176791390F51C"
auth_string = f"{account_number}:{license_key}"
auth_base64 = base64.b64encode(auth_string.encode()).decode()

salesforce = Salesforce(username=username, password=password, security_token=security_token)

company_code = 157753
transaction_code = "IN105483"


class Command(BaseCommand):
    def handle(self, *args, **options):
        sf_quote_list_raw = salesforce.query_all("SELECT Id, QuoteNumber, division__c, Opp_Close_Date__c, Bistrack_Order_Stage_Last_Change__c, AccountId, Total_plus_tax__c, Tax_Amount__c, is_delivery__c, delivery_address_validated__c, delivery_city_validated__c, delivery_postal_code_validated__c, delivery_state_validated__c FROM Quote WHERE (Bistrack_Order_Stage_Last_Change__c > 2025-01-31T20:00:00Z AND Bistrack_Order_Stage_Last_Change__c < 2025-03-01T00:00:00Z) AND IsSyncing = TRUE AND (Bistrack_Order_Stage__c = 'invoiced')")
        sf_quote_list = sf_quote_list_raw['records']

        row_count = 0
        tax_total = 0
        for quote in sf_quote_list:
            row_count += 1
            if row_count > 3:
                break
            sf_id = quote['Id']
            quote_number = quote['QuoteNumber']
            sf_division = quote['division__c']
            opp_close_date = quote['Opp_Close_Date__c']
            bistrack_stage_datetime = quote['Bistrack_Order_Stage_Last_Change__c']
            dt = datetime.strptime(bistrack_stage_datetime, "%Y-%m-%dT%H:%M:%S.%f%z")
            bistrack_stage_date = dt.strftime("%Y-%m-%d")
            customer_id = quote['AccountId']
            
            quote_amount = quote['Total_plus_tax__c']
            tax_amount = quote.get('Tax_Amount__c', 0)  # Default to 0 if the field is null
            if tax_amount == 0.00:
                exemption_code = "Exempt"
            else:
                exemption_code = ""
            is_delivery = quote['is_delivery__c']
            if sf_division == "Wheat Ridge" or sf_division == "Outside Sales":
                ship_from_street = "11722 W 44th Ave"
                ship_from_state = "CO"
                ship_from_city = "Wheat Ridge"
                ship_from_postal_code = "80033"
                ship_from_country = "US"
            elif sf_division == "Tabor":
                ship_from_street = "5075 Tabor St"
                ship_from_state = "CO"
                ship_from_city = "Wheat Ridge"
                ship_from_postal_code = "80033"
                ship_from_country = "US"
            else:
                ship_from_street = "10605 Charter Oak Ranch Rd"
                ship_from_state = "CO"
                ship_from_city = "Fountain"
                ship_from_postal_code = "80817"
                ship_from_country = "US"

            if is_delivery == "NO":
                shipping_street = ship_from_street
                shipping_state = ship_from_state
                shipping_city = ship_from_city
                shipping_postal_code = ship_from_postal_code
                shipping_country = ship_from_country
            else:
                shipping_street = quote.get('delivery_address_validated__c', '')
                shipping_state = quote.get('delivery_state_validated__c', '')
                shipping_city = quote.get('delivery_city_validated__c', '')
                shipping_postal_code = quote.get('delivery_postal_code_validated__c', '')
                shipping_country = 'US'

            print(f"ID: {sf_id}, Quote Number: {quote_number}, Close Date: {opp_close_date}, "
            f"Customer ID: {customer_id}, Total: {quote_amount}, Tax: {tax_amount}, Is Delivery: {is_delivery}, "
            f"Address: {shipping_street}, {shipping_city}, {shipping_state}, {shipping_postal_code}, {shipping_country}")
            row_count += 1
            tax_total += tax_amount

            sf_quote_line_item_list_raw = salesforce.query_all(
                f"""
                SELECT Id, LineNumber, QuoteId, bistrack_product_code__c, Quantity, TotalPrice, Revised_Name__c, product_name__c
                FROM QuoteLineItem
                WHERE QuoteId = '{sf_id}'
                AND (product_name__c != '# LINE ITEM NOTE' AND product_name__c != '# LINE ITEM LABEL')
                """
            )


            sf_quote_line_item_list = sf_quote_line_item_list_raw['records']

            quote_line_count = 1
            quote_line_item_list = []
            for line_item in sf_quote_line_item_list:
                line_item_id = line_item['Id']
                quote_id = line_item['QuoteId']
                line_item_number = line_item['LineNumber']
                product_code = line_item.get('bistrack_product_code__c', '')  # Default to empty string if null
                quantity = line_item.get('Quantity', 0)  # Default to 0 if null
                line_item_total = line_item.get('TotalPrice', 0.0)  # Default to 0.0 if null
                product_name = line_item.get('product_name__c', '')
                if "# DELIVERY" in product_name:
                    tax_code = "NT"
                    product_code = "DC"
                else:
                    tax_code = "P0000000"

                if "# SPECIAL ORDER" in product_name:
                    product_name = line_item['Revised_Name__c']
                else:
                    pass


                quote_line_data = {
                    "number": line_item_number,
                    "quantity": quantity,
                    "amount": line_item_total,
                    "taxCode": tax_code,
                    "itemCode": product_code,
                    "description": product_name
                    }
                quote_line_item_list.append(quote_line_data)

            quote_data = {
                "lines": quote_line_item_list,
                "type": "SalesInvoice",
                "companyCode": company_code,
                "date": bistrack_stage_date,
                "customerCode": customer_id,
                "docCode": quote_number,
                "exemptionNo": exemption_code,
                "totalAmount": quote_amount,
                "totalTax": tax_amount,
                "addresses": {
                    "shipFrom": {
                        "line1": ship_from_street,
                        "city": ship_from_city,
                        "region": ship_from_state,
                        "country": shipping_country,
                        "postalCode": ship_from_postal_code
                    },
                    "shipTo": {
                        "line1": shipping_street,
                        "city": shipping_city,
                        "region": shipping_state,
                        "country": shipping_country,
                        "postalCode": shipping_postal_code
                    }
                },
                "commit": True,
                "currencyCode": "USD",
                }

            # url = "https://rest.avatax.com/api/v2/transactions/create"
            #
            payload = json.dumps(quote_data)
            #
            # headers = {
            #     'X-Avalara-Client': 'DjangoTaxApp; 1.0; Production; Self',
            #     'Authorization': f'Basic {auth_base64}',
            #     'Content-Type': 'application/json'
            # }
            #
            # response = requests.request("POST", url, headers=headers, data=payload, allow_redirects=False)

            print(payload)

