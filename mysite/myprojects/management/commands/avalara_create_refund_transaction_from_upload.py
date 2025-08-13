# taxes/management/commands/import_avalara_credit_notes.py

from django.core.management.base import BaseCommand
import pandas as pd
from datetime import datetime
import base64
import json
import requests
import csv
from pathlib import Path

class Command(BaseCommand):
    help = "Import credit notes (refunds) from CSV and send transactions to Avalara as ReturnInvoice"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        df = pd.read_csv(csv_path)

        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True)

        account_number = 2000899182
        license_key = "CFF176791390F51C"
        company_code = 157753

        auth_string = f"{account_number}:{license_key}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/json",
            "X-Avalara-Client": "DjangoTaxApp; 1.0; Production; Self"
        }

        grouped = df.groupby("CreditNoteID")

        error_log = []
        error_log_path = Path("avalara_credit_errors.csv")

        row_count = 0
        for credit_id, group in grouped:
            # row_count += 1
            # if row_count > 3:
            #     break
            first = group.iloc[0]
            credit_date = pd.to_datetime(first["CreditDate"]).strftime("%Y-%m-%d")
            customer_code = str(first["CustomerID"])
            branch_id = int(first["BranchID"])

            total_amount = group["TotalAmount"].sum()
            total_tax = group["TotalTax"].sum()
            exemption_code = "Exempt" if total_tax == 0 else ""

            # Ship-from (based on BranchID)
            if branch_id == 2:
                ship_from = {
                    "line1": "11722 W 44th Ave",
                    "city": "Wheat Ridge",
                    "region": "CO",
                    "country": "US",
                    "postalCode": "80033",
                }
            elif branch_id == 3:
                ship_from = {
                    "line1": "10605 Charter Oak Ranch Rd",
                    "city": "Fountain",
                    "region": "CO",
                    "country": "US",
                    "postalCode": "80817",
                }
            else:
                ship_from = {
                    "line1": "5075 Tabor St",
                    "city": "Wheat Ridge",
                    "region": "CO",
                    "country": "US",
                    "postalCode": "80033",
                }

            # Use structured delivery address if present
            if first["DeliveryAddressLine1"]:
                ship_to = {
                    "line1": first["DeliveryAddressLine1"],
                    "city": first["DeliveryCity"],
                    "region": first["DeliveryCounty"],
                    "country": "US",
                    "postalCode": first["DeliveryPostCode"]
                }
            else:
                ship_to = ship_from.copy()

            # Build line items
            lines = []
            for _, row in group.iterrows():
                description = str(row["Description"])
                product_code = str(row["ProductID"])

                if "DC - Delivery Charge" in description:
                    tax_code = "NT"
                    product_code = "DC"
                else:
                    tax_code = "P0000000"

                lines.append({
                    "number": str(row["CreditNoteLineID"]),
                    "quantity": int(row["Quantity"]),
                    "amount": -1 * float(row["TotalAmount"]),
                    "taxCode": tax_code,
                    "itemCode": product_code,
                    "description": description
                })

            transaction_data = {
                "type": "ReturnInvoice",
                "companyCode": company_code,
                "date": credit_date,
                "customerCode": customer_code,
                "docCode": str(credit_id),
                "exemptionNo": exemption_code,
                "totalAmount": total_amount,
                "totalTax": total_tax,
                "currencyCode": "USD",
                "commit": True,
                "addresses": {
                    "shipFrom": ship_from,
                    "shipTo": ship_to
                },
                "lines": lines
            }

            response = requests.post(
                "https://rest.avatax.com/api/v2/transactions/create",
                headers=headers,
                data=json.dumps(transaction_data)
            )

            if response.status_code >= 400:
                error_message = response.json().get("error", {}).get("message", "Unknown error")
                self.stdout.write(self.style.ERROR(f"[Credit {credit_id}] ERROR: {error_message}"))
                error_log.append({
                    "CreditNoteID": credit_id,
                    "StatusCode": response.status_code,
                    "ErrorMessage": error_message,
                    "FullResponse": response.text
                })
            else:
                self.stdout.write(self.style.SUCCESS(f"[Credit {credit_id}] Submitted successfully."))

            # payload = json.dumps(transaction_data)
            # print(payload)

        if error_log:
            with open(error_log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=error_log[0].keys())
                writer.writeheader()
                writer.writerows(error_log)
            self.stdout.write(self.style.WARNING(
                f"{len(error_log)} credit notes failed. See {error_log_path.resolve()}"))
        else:
            self.stdout.write(self.style.SUCCESS("All credit notes submitted successfully!"))
