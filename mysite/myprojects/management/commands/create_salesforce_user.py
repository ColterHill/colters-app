from simple_salesforce import Salesforce
from django.core.management.base import BaseCommand
from datetime import datetime


username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

sf = Salesforce(username=username, password=password, security_token=security_token)


class Command(BaseCommand):
    def handle(self, *args, **options):

        # Example values (must be adapted to your org)
        user_data = {
            'Username': 'rmfpdriver1@rmfp.com',
            'FirstName': 'Test',
            'LastName': 'User',
            'Alias': 'tuser',
            'Email': 'rmfpdriver1@rmfp.com',
            'TimeZoneSidKey': 'America/Denver',
            'LocaleSidKey': 'en_US',
            'EmailEncodingKey': 'UTF-8',
            'LanguageLocaleKey': 'en_US',
            'Division': 'Inside Sales - WR',
            'RMFP_Department__c': 'Sales',
            'ProfileId': '00e800000011YJs',  # Inside Sales - WR
            'rmfp_division_for_reporting__c': 'Wheat Ridge',
            'UserPermissionsMarketingUser': True,
            'IsActive': True
        }

        # Create the user
        result = sf.User.create(user_data)

        print(result)
