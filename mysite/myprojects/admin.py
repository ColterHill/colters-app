from django.contrib import admin
from .models import MarketingTracker, SmsTracker, PhoneCalls, EnneagramCode, EnneagramTest

# Register your models here.
class MarketingTrackerAdmin(admin.ModelAdmin):
    list_display = ('id', 'campaign_code', 'phone_source', 'number_called_name', 'keyword')
    list_filter = ('campaign_code',)

class PhoneCallsAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_number', 'tracking_number', 'sentiment')

admin.site.register(MarketingTracker, MarketingTrackerAdmin)
admin.site.register(SmsTracker)
admin.site.register(PhoneCalls, PhoneCallsAdmin)

class EnneagramTestAdmin(admin.ModelAdmin):
    list_display = ['invited', 'status', 'fullname', 'email', 'test_taken_date', 'enneagram_code', 'result_1', 'result_2', 'result_3']
admin.site.register(EnneagramTest, EnneagramTestAdmin)


class EnneagramCodeAdmin(admin.ModelAdmin):
    list_display = ['expiration', 'status', 'code']
admin.site.register(EnneagramCode, EnneagramCodeAdmin)