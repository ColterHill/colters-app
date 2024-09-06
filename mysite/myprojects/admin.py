from django.contrib import admin
from .models import MarketingTracker, SmsTracker

# Register your models here.
admin.site.register(MarketingTracker)
admin.site.register(SmsTracker)