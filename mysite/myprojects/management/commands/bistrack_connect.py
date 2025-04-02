from django.core.management.base import BaseCommand
import requests
from django.core.exceptions import ObjectDoesNotExist
from simple_salesforce import Salesforce
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone as django_tz
from datetime import datetime, date, time, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import json

bt_base_url = 'https://rockymountainportal.epicoranywhere.com/BisTrackWebStoreAPI'
bt_api_key = 'A5B6126183F9DJPW094MFGKUASTQ429CDN40239DKSAL561J7EC8CD9737910E24'
bt_data = {"client_secret": "A5B6126183F9DJPW094MFGKUASTQ429CDN40239DKSAL561J7EC8CD9737910E24"}
bt_resp = requests.post(f'{bt_base_url}/api/authenticate', data=bt_data, params={'api_key': bt_api_key})
access_token = bt_resp.json()['AccessToken']
sess = requests.Session()
sess.headers["Authorization"] = f'Bearer {access_token}'

salesforce = Salesforce(username='bbrooke@rmfp.com', password='rmfp2016!', security_token='Eo0K7FUAbag0pekcjEzNbBACv')

class Command(BaseCommand):
    def handle(self, *args, **options):

        resp_dict_raw = sess.get(f'{bt_base_url}/api/product/776')
        print(resp_dict_raw.json())
