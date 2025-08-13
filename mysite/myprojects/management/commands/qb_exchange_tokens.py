# management/commands/qbo_exchange_tokens.py

from django.core.management.base import BaseCommand
from intuitlib.client import AuthClient
from django.conf import settings
from myprojects.models import QuickBooksToken  # or however you store tokens

class Command(BaseCommand):
    help = 'Exchange a QBO code for tokens'

    def add_arguments(self, parser):
        parser.add_argument('--code', required=True, help='Authorization code from QBO')
        parser.add_argument('--realm_id', required=True, help='Company ID from QBO')

    def handle(self, *args, **options):
        code = options['code']
        realm_id = options['realm_id']

        auth_client = AuthClient(
            client_id=settings.QBO_CLIENT_ID,
            client_secret=settings.QBO_CLIENT_SECRET,
            environment='production',
            redirect_uri='https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
        )

        try:
            auth_client.get_bearer_token(code, realm_id=realm_id)

            QuickBooksToken.objects.update_or_create(
                company_id=realm_id,
                defaults={
                    'access_token': auth_client.access_token,
                    'refresh_token': auth_client.refresh_token,
                }
            )

            self.stdout.write(self.style.SUCCESS('✅ Tokens saved successfully.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Token exchange failed: {e}'))
