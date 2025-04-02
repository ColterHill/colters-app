from django.core.management.base import BaseCommand
from myprojects.models import MarketingTracker
from avalara import AvataxClient
from datetime import datetime, date, time, timedelta
import math
from simple_salesforce import Salesforce
import pytz
import re
from operator import itemgetter
import requests
import base64
import json
import os
from decimal import Decimal
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
        url = f"https://rest.avatax.com/api/v2/companies/{company_code}/transactions/IN105483"

        payload = {}
        headers = {
            'X-Avalara-Client': 'DjangoTaxApp; 1.0; Production; Self',
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload, allow_redirects=False)

        print(response.text)