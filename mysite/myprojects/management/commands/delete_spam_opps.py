from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
import re

class Command(BaseCommand):
    help = 'Delete spam opportunities for a specific sales rep (e.g., Ryan Chavez)'

    def handle(self, *args, **kwargs):
        # Set to True to skip actual deletion during testing
        DRY_RUN = False

        # --- Salesforce login ---
        username = 'chill@rmfp.com'
        password = 'RMFP2023a!'
        security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'

        sf = Salesforce(username=username, password=password, security_token=security_token)

        # --- Query opportunities assigned to Ryan Chavez ---
        query = """
            SELECT Id, Name, OwnerId, account_first_name__c, account_last_name__c
            FROM Opportunity
            WHERE OwnerId = '0050y00000E05IBAAZ' AND Leading_Quote_Amount__c = 0 AND StageName = 'Closed Lost'
        """
        results = sf.query_all(query)
        opps = results['records']

        self.stdout.write(f"Total opportunities found: {len(opps)}")



        # --- Spam filter logic ---
        def is_spam(first_name, last_name):
            if not first_name or not last_name:
                return False  # Skip nulls

            first = first_name.strip().lower()
            last = last_name.strip().lower()

            # 1. Last name starts with first and is just a few characters longer
            if last.startswith(first) and len(last) <= len(first) + 4:
                return True

            # 2. Obvious junk content
            combined = f"{first} {last}"
            if re.search(r'(test|asdf|demo|qwer|xyz|1234)', combined):
                return True

            # 3. Repetitive character patterns (e.g., "RobertRobert", "GobGobGob")
            if re.match(r'(\w{2,})\1{1,}', combined.replace(" ", "")):
                return True

            return False

        spam_opps = [
            opp for opp in opps
            if is_spam(opp.get('account_first_name__c'), opp.get('account_last_name__c'))
        ]

        self.stdout.write(f"Spam opportunities identified: {len(spam_opps)}")

        # --- Delete spam opps ---
        for opp in spam_opps:
            opp_id = opp['Id']
            opp_name = opp['Name']
            acct_first_name = opp['account_first_name__c']
            acct_last_name = opp['account_last_name__c']
            try:
                if DRY_RUN:
                    self.stdout.write(f"[Dry Run] Would delete: {opp_name} ({opp_id})")
                    self.stdout.write("Account Name: %s %s" % (acct_first_name, acct_last_name))
                else:
                    sf.Opportunity.delete(opp_id)
                    self.stdout.write(f"Deleted: {opp_name} ({opp_id})")
            except Exception as e:
                self.stderr.write(f"Error deleting {opp_id}: {e}")
