from django.core.management.base import BaseCommand
import requests
import base64


class Command(BaseCommand):
    help = 'Pull transactions from Avalara for February 2025'

    def handle(self, *args, **options):
        # Avalara API credentials
        account_number = 2000899182
        license_key = "CFF176791390F51C"
        company_code = 157753
        auth_string = f"{account_number}:{license_key}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()

        # Define the URL and query parameters
        url = f"https://rest.avatax.com/api/v2/companies/{company_code}/transactions"
        params = {
            "startDate": "2025-02-01",
            "endDate": "2025-02-28",
            # Optionally, add more filters (for example, to limit to SalesInvoices)
            # "transactionType": "SalesInvoice"
        }
        headers = {
            'X-Avalara-Client': 'DjangoTaxApp; 1.0; Production; Self',
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/json'
        }

        self.stdout.write("Requesting transactions from Avalara for February 2025...")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            transactions = data.get('value', [])
            self.stdout.write(self.style.SUCCESS(f"Retrieved {len(transactions)} transactions."))

            # If there is pagination, check for a nextLink (optional)
            next_link = data.get('@odata.nextLink')
            while next_link:
                next_response = requests.get(next_link, headers=headers)
                if next_response.status_code == 200:
                    next_data = next_response.json()
                    transactions.extend(next_data.get('value', []))
                    next_link = next_data.get('@odata.nextLink')
                else:
                    self.stdout.write(self.style.ERROR(f"Error retrieving next page: {next_response.status_code}"))
                    break

            # Output each transaction (or handle them as needed)
            for txn in transactions:
                self.stdout.write(str(txn))
        else:
            self.stdout.write(self.style.ERROR(f"Error retrieving transactions: {response.status_code}"))
