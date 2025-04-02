from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Your API Key
        API_KEY = "477ac881b043df62d5b0d7104db1fbd2"
        ACCOUNT_ID = "227527750"

        url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/trackers.json"

        # Headers
        headers = {
            "Authorization": f"Token token={API_KEY}",
            "Content-Type": "application/json"
        }

        # Make the API Request
        response = requests.get(url, headers=headers)

        # Process Response
        if response.status_code == 200:
            data = response.json()
            
            print("Tracking Numbers:")
            for number in data['numbers']:
                print(f"Name: {number['name']}, Number: {number['phone_number']}")
        else:
            print(f"Error {response.status_code}: {response.text}")