import sys
from django.core.management.base import BaseCommand
from django.shortcuts import get_list_or_404, get_object_or_404
from users.models import Profile
from myprojects.models import SmsTracker
from datetime import datetime
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from ringcentral import SDK
from simple_salesforce import Salesforce
import re


username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

salesforce = Salesforce(username=username, password=password, security_token=security_token)

rc_client_id = '5vxdcVrb7bPcT45tDxjZop'
rc_client_secret = 'XpBmr5OBiVZcYbvwP9mVX5Xp6AaDoqa5ZcGQ8MLpVjjJ'
rc_server_url = 'https://platform.ringcentral.com'

sdk = SDK(rc_client_id, rc_client_secret, rc_server_url)
platform = sdk.platform()


def clean_phone(phone_raw):
    """
    1) Can't always see float decimal from excel so this strip  the ".0" at end
    2) remove "1" from beginning of phone number if added
    3) If not 10 digit number return " "
    """
    if isinstance(phone_raw, float):
        phone_raw = str(phone_raw)[:10]
    else:
        phone_raw = re.sub(r'\D', "", str(phone_raw))
    if str(phone_raw)[:1] == "1":
        phone_raw = str(phone_raw)[-10:]
    if len(phone_raw) != 10:
        phone_raw = ""
    return phone_raw


class Command(BaseCommand):
    def handle(self, *args, **options):
        profile_list = Profile.objects.all()
        for profile in profile_list:
            if profile.user.is_active == True:
                jwt_code = profile.ringcentral_jwt_code

                print(jwt_code)