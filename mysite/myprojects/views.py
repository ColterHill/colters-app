from django.shortcuts import render
from rest_framework import viewsets
from .models import MarketingTracker
from .api import MarketingTrackerSerializer
from intuitlib.client import AuthClient
from django.http import JsonResponse
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
