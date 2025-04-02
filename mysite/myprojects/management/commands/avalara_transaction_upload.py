from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
import requests
import base64
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
        uploaded_file_name = 'BT Invoices Feb 2025.csv'
        # Get, open and read file - use file path
        data = pd.read_csv(r'/Users/colterhill/Documents/Tax Data/Avalara Transactions Uploads/%s' % uploaded_file_name)

        df = pd.DataFrame(data)
        df = df.reset_index()  # Ensure indexes match number of rows

        # Fill missing address fields with an empty string
        address_cols = ['DeliveryAddressLine1', 'DeliveryCity', 'DeliveryCounty', 'DeliveryPostCode']
        df[address_cols] = df[address_cols].fillna("")

        # Option 1: Print overall totals directly from DataFrame
        overall_total_amount = df['TotalAmount'].sum()
        overall_total_tax = df['TotalTax'].sum()
        print(f"Overall CSV Totals - Total Amount: {overall_total_amount}, Total Tax: {overall_total_tax}")

        # Group by InvoiceID, assuming each invoice has one sale type and delivery address info
        grouped = df.groupby('InvoiceID')

        row_count = 0
        # Option 2: Accumulators for totals as you process invoices
        processed_total_amount = 0
        processed_total_tax = 0

        for invoice_id, group in grouped:
            # Retrieve the sale type from the first row of the group
            sale_type = group['SaleType'].iloc[0]

            lines = []
            # Process each invoice line
            for _, row in group.iterrows():
                branch_id = int(row['BranchID'])
                invoice_date = row['InvoiceDate']
                customer_id = row['CustomerID']
                line_item_id = str(row['InvoiceLineID'])
                item_quantity = row['Quantity']
                line_item_amount = row['TotalAmount']
                product_id = str(row['ProductID'])
                item_description = row['Description']
                total_tax = row['TotalTax']

                # Accumulate totals for processed invoices
                processed_total_amount += line_item_amount
                processed_total_tax += total_tax

                if total_tax == 0.00:
                    exemption_code = "Exempt"
                    tax_code = "NT"
                else:
                    exemption_code = ""
                    tax_code = "P0000000"

                # Determine the ship-from address based on branch
                if branch_id == 2:
                    ship_from_street = "11722 W 44th Ave"
                    ship_from_state = "CO"
                    ship_from_city = "Wheat Ridge"
                    ship_from_postal_code = "80033"
                else:
                    ship_from_street = "10605 Charter Oak Ranch Rd"
                    ship_from_state = "CO"
                    ship_from_city = "Fountain"
                    ship_from_postal_code = "80817"

                lines.append({
                    "number": line_item_id,
                    "quantity": item_quantity,
                    "amount": line_item_amount,
                    "itemCode": product_id,
                    "description": item_description,
                    "taxCode": tax_code,
                    "exemptionNo": exemption_code,
                })

            # For the ship-to address, use the delivery address if sale_type equals 3 (delivery)
            if sale_type == 3:
                # Extract delivery address columns from the first row of the group
                delivery_street = group['DeliveryAddressLine1'].iloc[0]
                delivery_city = group['DeliveryCity'].iloc[0]
                delivery_state = group['DeliveryCounty'].iloc[0]
                delivery_zip = group['DeliveryPostCode'].iloc[0]
            else:
                # For will call orders, use the ship-from address as ship-to
                delivery_street = ship_from_street
                delivery_city = ship_from_city
                delivery_state = ship_from_state
                delivery_zip = ship_from_postal_code

            payload = {
                "type": "SalesInvoice",
                "companyCode": company_code,
                "date": invoice_date,  # Ensure the date format is acceptable to Avalara
                "customerCode": f"CUST{int(customer_id)}",
                "docCode": f"IN{int(invoice_id)}",
                "commit": True,
                "addresses": {
                    "shipFrom": {
                        "line1": ship_from_street,
                        "city": ship_from_city,
                        "region": ship_from_state,
                        "country": "US",
                        "postalCode": ship_from_postal_code
                    },
                    "shipTo": {
                        "line1": delivery_street,
                        "city": delivery_city,
                        "region": delivery_state,
                        "country": "US",
                        "postalCode": delivery_zip
                    }
                },
                "lines": lines,

            }

            row_count += 1
            if row_count > 10:
                break

            url = "https://rest.avatax.com/api/v2/transactions/create"
            headers = {
                'X-Avalara-Client': 'DjangoTaxApp; 1.0; Production; Self',
                'Authorization': f'Basic {auth_base64}',
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers, json=payload)
            print(f"Transaction for InvoiceID {invoice_id}: {response.status_code}")

        print(f"Processed {row_count} invoices.")
        print(f"Processed Totals - Total Amount: {processed_total_amount}, Total Tax: {processed_total_tax}")