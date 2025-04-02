from .models import MarketingTracker
from rest_framework import serializers

class MarketingTrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingTracker
        fields = ['id', 'account_name', 'created', 'salesforce_account_id', 'campaign_code', 'phone_source', 'keyword', 'call_date', 'number_called_name']
        # fields = '__all__'