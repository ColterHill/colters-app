import requests
from requests.auth import HTTPBasicAuth
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Avalara API credentials
        account_number = 2000899182
        license_key = "CFF176791390F51C"

        # Base URL for the Avalara API (use the production URL when going live)
        base_url = "https://rest.avatax.com/api/v2"

        # API endpoint for testing (e.g., get tax rates by address)
        endpoint = "/taxrates/byaddress"

        # Parameters for the request (e.g., address)
        params = {
            "line1": "11722 ",
            "city": "Wheat Ridge",
            "region": "CO",
            "postalCode": "80033",
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

        print(total_tax)
        print(rates)
        for rate in rates:
            rate_amount = rate['rate']
            rate_name = rate['name']
            rate_type = rate['type']
            print(f"Amount: {rate_amount}, Name: {rate_name}, Type: {rate_type}")

        # # Check the response status code
        # if response.status_code == 200:
        #     print("Tax rate:", response.json())
        # else:
        #     print(f"Error: {response.status_code}, {response.text}")