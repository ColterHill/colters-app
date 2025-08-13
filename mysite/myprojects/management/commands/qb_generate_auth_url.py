# management/commands/qbo_generate_auth_url.py

from django.core.management.base import BaseCommand
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate QBO auth URL and print it to console'

    def handle(self, *args, **options):
        auth_client = AuthClient(
            client_id=settings.QBO_CLIENT_ID,
            client_secret=settings.QBO_CLIENT_SECRET,
            environment='production',
            redirect_uri='https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'  # This is OK to use here
        )

        scopes = [Scopes.ACCOUNTING]
        auth_url = auth_client.get_authorization_url(scopes)

        print(f"\nVisit this URL in your browser to connect to QBO:\n{auth_url}")
        print("After approving access, copy the 'code' and 'realmId' from the redirect URL.\n")
