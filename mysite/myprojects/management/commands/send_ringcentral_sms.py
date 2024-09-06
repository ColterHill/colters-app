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

        sf_top_150_raw = salesforce.query("SELECT Id, Name, phone_clean__c, Mobile_1__c, Rep_RingCentral__c, Rep_JWT_Code__c, Owner_Name__c FROM Account WHERE is_150_account_base_text__c = 'YES' AND (Owner_ID__pc = '0055c000008qMzkAAE' OR Owner_ID__pc = '0055c000008qwDVAAY')")
        sf_top_150 = sf_top_150_raw['records']

       
        for account_dict in sf_top_150:
            account_id = account_dict['Id']
            account_name = account_dict['Name']
            phone_clean = account_dict['phone_clean__c']
            account_mobile = account_dict['Mobile_1__c']
            mobile_clean = clean_phone(account_mobile)
            rep_phone = account_dict['Rep_RingCentral__c']
            rep_phone_clean = clean_phone(rep_phone)
            rep_phone_rc_match = "+1" + rep_phone_clean
            rep_jwt_code = account_dict['Rep_JWT_Code__c']
            rep_name = account_dict['Owner_Name__c']

            # To pick the "To" phone number. Check if account has a mobile #, if not, send to main phone
            if mobile_clean is (None or ""):
                to_number = phone_clean
            if mobile_clean is not (None or ""):
                to_number = mobile_clean
            # logs rep account into RingCentral using JWT code
            try:
                platform.login( jwt=rep_jwt_code )
                print("login worked")
            except Exception as e:
                sys.exit("Unable to authenticate to platform. Check credentials." + str(e))

            # Searches for the Rep's phone number within RingCentral
            try:
                resp = platform.get("/restapi/v1.0/account/~/extension/~/phone-number")
                jsonObj = resp.json()
                for record in jsonObj.records:
                    for feature in record.features:
                        # reps have multiple numbers in RC. So we need to pick the one that matches their main #
                        if feature == "SmsSender" and (rep_phone_rc_match == record.phoneNumber):
                            sms_tracker, is_new = SmsTracker.objects.get_or_create(account_to_number=to_number)

                            if is_new:
                                sms_tracker.account_to_number = to_number
                                sms_tracker.salesforce_account_id = account_id
                                sms_tracker.salesforce_account_name = account_name
                                sms_tracker.rep_name = rep_name
                                sms_tracker.rep_from_number = rep_phone_rc_match

                                sms_tracker.save(update_fields=['account_to_number', 'salesforce_account_id', 'salesforce_account_name', 'rep_name', 'rep_from_number'])
                            
                                try:
                                    bodyParams = {
                                        'from' : { 'phoneNumber': rep_phone_rc_match },
                                        'to'   : [ {'phoneNumber': to_number} ],
                                        'text' : f"Hello {account_name}! Here is test Text"
                                    }
                                    endpoint = "/restapi/v1.0/account/~/extension/~/sms"
                                    resp = platform.post(endpoint, bodyParams)
                                    jsonObj = resp.json()
                                    print ("SMS sent. Message id: " + str(jsonObj.id))
                                except Exception as e:
                                    print (e)

            except Exception as e:
                print (e)