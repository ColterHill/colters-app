from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
from datetime import datetime, date, time, timedelta
import math
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
        uploaded_file_name = 'BT Refunds Feb 2025.csv'

        # Get, open and read file - use file path
        """
        IMPORTANT update file name and update campaign name below
        """
        data = pd.read_csv(r'/Users/colterhill/Documents/Tax Data/Avalara Transactions Uploads/%s' % uploaded_file_name)

        df = pd.DataFrame(data)

        df = df.reset_index()  # make sure indexes pair with number of rows

        grouped = data.groupby('CreditNoteID')

        credit_note_list = []
        seen = set()
        row_count = 0
        for credit_note_id, group in grouped:
            # Prepare transaction payload
            lines = []
            for _, row in group.iterrows():
                branch_id = int(row['BranchID'])
                credit_date = row['CreditDate']
                customer_id = row['CustomerID']
                line_item_id = str(row['CreditNoteLineID'])
                item_quantity = row['Quantity']
                line_item_amount = row['TotalAmount'] * -1
                product_id = str(row['ProductID'])
                item_description = row['Description']
                total_tax = row['TotalTax']
                if total_tax == 0.00:
                    exemption_code = "Exempt"
                else:
                    exemption_code = ""

                if branch_id == 2:
                    ship_from_street = "11722 W 44th Ave"
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

                lines.append({
                    "number": line_item_id,
                    "quantity": item_quantity,
                    "amount": line_item_amount,
                    "itemCode": product_id,
                    "description": item_description,
                    "taxCode": "P0000000",  # Default tax code, adjust as needed
                })

            payload = {
                "type": "ReturnInvoice",
                "companyCode": company_code,
                "date": credit_date,  # Adjust based on your requirements
                "customerCode": f"CUST{int(customer_id)}",
                "docCode": f"CN{int(credit_note_id)}",
                "exemptionNo": exemption_code,
                "addresses": {
                    "shipFrom": {
                        "line1": ship_from_street,
                        "city": ship_from_city,
                        "region": ship_from_state,
                        "country": "US",
                        "postalCode": ship_from_postal_code
                    },
                    "shipTo": {
                        "line1": ship_from_street,
                        "city": ship_from_city,
                        "region": ship_from_state,
                        "country": "US",
                        "postalCode": ship_from_postal_code
                    }
                },
                "lines": lines,
                "commit": True
            }

            row_count += 1
            # print(credit_note_id)
            # print(credit_date)
            # print(payload)

            url = "https://rest.avatax.com/api/v2/transactions/create"

            headers = {
                'X-Avalara-Client': 'DjangoTaxApp; 1.0; Production; Self',
                'Authorization': f'Basic {auth_base64}',
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers, json=payload)
            print(f"Transaction for CreditNoteID {credit_note_id}: {response.status_code}, {response.json()}")
        print(row_count)