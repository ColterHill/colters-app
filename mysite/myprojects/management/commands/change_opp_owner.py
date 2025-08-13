from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
import os

class Command(BaseCommand):
    help = 'Update opportunity owner from one user to another in Salesforce'

    def handle(self, *args, **kwargs):
        # You should securely store these credentials in env variables or Django settings
        username = 'chill@rmfp.com'
        password = 'RMFP2023a!'
        security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
        sf = Salesforce(username=username, password=password, security_token=security_token)

        # Replace with actual Salesforce User IDs
        bryant_user_id = '005Um000001pz5h'  # Bryant Aguilera's Salesforce User ID
        blake_user_id = '005C0000003is5y'   # Blake Rogers' Salesforce User ID
        nick_eddy_user_id = '005Um000002OJJh' # Nick Eddy's Salesforce User ID
        jesse_coates_user_id = '005C0000007uCRm'  # Jesse Coates' Salesforce User ID

        query = f"SELECT Id, Name FROM Opportunity WHERE OwnerId = '{nick_eddy_user_id}' AND StageName = 'Prospecting'"
        results = sf.query_all(query)
        opportunities = results['records']

        if not opportunities:
            self.stdout.write(self.style.WARNING("No opportunities found for Bryant Aguilera."))
            return

        self.stdout.write(f"Found {len(opportunities)} opportunities. Updating owner...")

        for opp in opportunities:
            opp_id = opp['Id']
            sf.Opportunity.update(opp_id, {'OwnerId': jesse_coates_user_id})
            self.stdout.write(f"Updated Opportunity {opp['Name']} ({opp_id})")

        self.stdout.write(self.style.SUCCESS("Finished updating opportunity owners."))
