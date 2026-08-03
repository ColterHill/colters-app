from django.shortcuts import render
from rest_framework import viewsets
from .models import MarketingTracker
from .api import MarketingTrackerSerializer
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from intuitlib.enums import Scopes
from intuitlib.client import AuthClient
from django.conf import settings
from .models import QuickBooksToken
import json
import os
from ringcentral import SDK
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


def ringcentral_recording_proxy(request, recording_id):
    """
    Proxy endpoint to stream RingCentral call recordings with authentication.
    Usage: /ringcentral/recording/<recording_id>/
    """
    # Default credentials path - you can make this configurable via settings
    credentials_path = os.path.expanduser('~/Downloads/rc-credentials.json')
    user_name = 'Colter Hill'  # Default user - you can make this configurable
    
    try:
        # Load credentials
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        client_id = credentials.get('clientId')
        client_secret = credentials.get('clientSecret')
        server = credentials.get('server', 'https://platform.ringcentral.com')
        jwt_tokens = credentials.get('jwt', {})
        jwt_token = jwt_tokens.get(user_name)
        
        if not client_id or not client_secret or not jwt_token:
            return JsonResponse({
                'error': 'RingCentral credentials not configured'
            }, status=500)
        
        # Initialize SDK and authenticate
        sdk = SDK(client_id, client_secret, server)
        platform = sdk.platform()
        platform.login(jwt=jwt_token)
        
        # Fetch the recording content
        # The recording path format: /restapi/v1.0/account/~/recording/{recording_id}/content
        recording_path = f'/restapi/v1.0/account/~/recording/{recording_id}/content'
        
        try:
            response = platform.get(recording_path)
            recording_content = response.body()
            
            # Determine content type (RingCentral recordings are typically MP3 or WAV)
            # Check response headers if available, otherwise default to MP3
            content_type = 'audio/mpeg'  # Default to MP3
            
            # Create streaming response
            http_response = HttpResponse(recording_content, content_type=content_type)
            http_response['Content-Disposition'] = f'inline; filename="recording_{recording_id}.mp3"'
            http_response['Content-Length'] = str(len(recording_content))
            
            return http_response
            
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to fetch recording: {str(e)}'
            }, status=500)
            
    except FileNotFoundError:
        return JsonResponse({
            'error': 'RingCentral credentials file not found'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': f'Error accessing recording: {str(e)}'
        }, status=500)