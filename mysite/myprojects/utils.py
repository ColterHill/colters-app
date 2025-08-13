# qbo/utils.py

from intuitlib.client import AuthClient
from django.conf import settings
from .models import QuickBooksToken

def get_valid_qbo_access_token(company_id: str):
    token = QuickBooksToken.objects.get(company_id=company_id)

    auth_client = AuthClient(
        client_id=settings.QBO_CLIENT_ID,
        client_secret=settings.QBO_CLIENT_SECRET,
        environment='production',
        redirect_uri=settings.QBO_REDIRECT_URI
    )
    auth_client.refresh_token = token.refresh_token

    # Refresh the token
    auth_client.refresh()

    # Save updated tokens
    token.access_token = auth_client.access_token
    token.refresh_token = auth_client.refresh_token
    token.save()

    return auth_client.access_token
