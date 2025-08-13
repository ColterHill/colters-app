from dotenv import load_dotenv
import os
from urllib.parse import quote
from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        load_dotenv()

        access_token = os.getenv('QBO_ACCESS_TOKEN')
        company_id = os.getenv('QBO_COMPANY_ID')

        query = "SELECT * FROM Account WHERE MetaData.LastUpdatedTime > '2014-09-17T15:28:48-07:00'"
        encoded_query = quote(query)

        url = f'https://quickbooks.api.intuit.com/v3/company/{company_id}/query?query={encoded_query}&minorversion=75'

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'text/plain',
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            for account in data.get('QueryResponse', {}).get('Account', []):
                company_name = account.get('Name', 'Unknown')
                account_id = account.get('Id', 'Unknown')


                print(f"Company Name: {company_name} | ID: {account_id} | ")

        except requests.RequestException as e:
            self.stderr.write(f"Request failed: {e}")