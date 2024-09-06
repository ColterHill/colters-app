from django.db import models
from django.utils import timezone as django_tz

# Create your models here.
class MarketingTracker(models.Model):
    created = models.DateTimeField(default=django_tz.now)
    salesforce_account_id = models.CharField(null=True, blank=True, max_length=18)
    campaign_code = models.CharField(null=True, blank=True, max_length=64)
    phone_source = models.CharField(null=True, blank=True, max_length=64)
    keyword = models.CharField(null=True, blank=True, max_length=150)



class SmsTracker(models.Model):
    sent_time = models.DateTimeField(default=django_tz.now)
    salesforce_account_id = models.CharField(null=True, blank=True, max_length=18)
    salesforce_account_name = models.CharField(null=True, blank=True, max_length=64)
    rep_name = models.CharField(null=True, blank=True, max_length=64)
    rep_from_number = models.CharField(null=True, blank=True, max_length=10)
    account_to_number = models.CharField(null=True, blank=True, max_length=10)