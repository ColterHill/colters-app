from django.core.management.base import BaseCommand
from avalara import AvataxClient
import requests
import base64

# Avalara API credentials
account_number = 2000899182
license_key = "CFF176791390F51C"
auth_string = f"{account_number}:{license_key}"
auth_base64 = base64.b64encode(auth_string.encode()).decode()

company_code = 157753
transaction_code = "IN105483"

client = AvataxClient('DjangoAvaTax', 'ver 1.0', 'Colters Laptop', 'Production')

class Command(BaseCommand):
    def handle(self, *args, **options):
        url = "https://rest.avatax.com/api/v2/utilities/ping"

        payload = {}
        headers = {
            'X-Avalara-Client': 'DjangoTaxApp; 1.0; Production; Self',
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload, allow_redirects=False)

        print(response.text)