from django.shortcuts import render
from rest_framework import viewsets
from .models import MarketingTracker
from .api import MarketingTrackerSerializer
from django.http import JsonResponse
from django.shortcuts import redirect
from intuitlib.enums import Scopes
from django.http import HttpResponse
from intuitlib.client import AuthClient
from django.conf import settings
from .models import QuickBooksToken
# Create your views here.

auth_client = AuthClient(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    environment='sandbox',  # Change to 'production' if applicable
    redirect_uri='http://localhost:8000/callback/',
)

class MarketingTrackerViewSet(viewsets.ModelViewSet):
    queryset = MarketingTracker.objects.all()
    serializer_class = MarketingTrackerSerializer


def quickbooks_callback(request):
    authorization_code = request.GET.get('code', None)

    if authorization_code:
        try:
            auth_client.get_bearer_token(authorization_code)
            return JsonResponse({
                "access_token": auth_client.access_token,
                "refresh_token": auth_client.refresh_token,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Authorization code not provided"}, status=400)

def qbo_connect(request):
    auth_client = AuthClient(
        client_id=settings.QBO_CLIENT_ID,
        client_secret=settings.QBO_CLIENT_SECRET,
        environment='production',  # or 'sandbox'
        redirect_uri=settings.QBO_REDIRECT_URI
    )

    scopes = [Scopes.ACCOUNTING]
    auth_url = auth_client.get_authorization_url(scopes)

    # Store auth_client.state if you want to verify on callback
    request.session['qbo_state'] = auth_client.state

    return redirect(auth_url)

def qbo_callback(request):
    code = request.GET.get('code')
    realm_id = request.GET.get('realmId')
    state = request.GET.get('state')

    # Optional: Validate state matches session['qbo_state']

    auth_client = AuthClient(
        client_id=settings.QBO_CLIENT_ID,
        client_secret=settings.QBO_CLIENT_SECRET,
        environment='production',
        redirect_uri=settings.QBO_REDIRECT_URI
    )

    auth_client.get_bearer_token(code, realm_id=realm_id)

    # Save tokens in DB
    token, created = QuickBooksToken.objects.update_or_create(
        company_id=realm_id,
        defaults={
            'access_token': auth_client.access_token,
            'refresh_token': auth_client.refresh_token,
        }
    )

    return HttpResponse(f"Successfully connected to QBO for company {realm_id}")