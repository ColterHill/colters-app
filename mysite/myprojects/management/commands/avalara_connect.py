import requests
from requests.auth import HTTPBasicAuth
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Test Avalara tax rate lookup"

    def handle(self, *args, **options):
        account_number = 2000899182
        license_key = "CFF176791390F51C"
        base_url = "https://rest.avatax.com/api/v2"
        endpoint = "/taxrates/byaddress"

        params = {
            "line1": "11722 W 44th Ave",
            "city": "Wheat Ridge",
            "region": "CO",
            "postalCode": "80033",
            "country": "US"
        }

        try:
            response = requests.get(
                base_url + endpoint,
                auth=HTTPBasicAuth(account_number, license_key),
                params=params
            )
            response.raise_for_status()
            tax_data = response.json()
            print("✅ Success:", tax_data)
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP error: {e}")
            print("Response content:", response.text)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
