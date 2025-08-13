from django.db import models
from django.utils import timezone as django_tz
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Q, PROTECT, SET_NULL, Sum


# Create your models here.
class MarketingTracker(models.Model):

    def __str__(self):
        return self.salesforce_account_id

    created = models.DateTimeField(default=django_tz.now)
    call_date = models.DateTimeField(null=True, blank=True)
    salesforce_account_id = models.CharField(null=True, blank=True, max_length=18)
    account_name = models.CharField(null=True, blank=True, max_length=64)
    campaign_code = models.CharField(null=True, blank=True, max_length=64)
    phone_source = models.CharField(null=True, blank=True, max_length=64)
    number_called_name = models.CharField(null=True, blank=True, max_length=64)
    keyword = models.CharField(null=True, blank=True, max_length=150)



class SmsTracker(models.Model):
    sent_time = models.DateTimeField(default=django_tz.now)
    salesforce_account_id = models.CharField(null=True, blank=True, max_length=18)
    salesforce_account_name = models.CharField(null=True, blank=True, max_length=64)
    rep_name = models.CharField(null=True, blank=True, max_length=64)
    rep_from_number = models.CharField(null=True, blank=True, max_length=10)
    account_to_number = models.CharField(null=True, blank=True, max_length=10)


class PhoneCalls(models.Model):
    
    def __str__(self):
        return self.customer_number

    call_date = models.DateTimeField(default=django_tz.now)
    duration = models.IntegerField(default=0)
    customer_number = models.CharField(null=True, blank=True, max_length=18)
    tracking_number = models.CharField(null=True, blank=True, max_length=18)
    tracking_number_name = models.CharField(null=True, blank=True, max_length=64)
    recording_url = models.CharField(null=True, blank=True, max_length=128)
    transcription = models.TextField(null=True, blank=True)
    sentiment = models.CharField(null=True, blank=True, max_length=128)


class EnneagramTest(models.Model):
    invited = models.DateTimeField(default=django_tz.now)
    status = models.IntegerField(choices=[
        (0, 'pending'),
        (1, 'complete'),
        (2, 'canceled'),
        (3, 'expired'),
    ], default=0)
    department = models.IntegerField(choices=[
        (0, 'other'),
        (1, 'sales'),
        (2, 'ops'),
    ], default=0)
    enneagram_code = models.ForeignKey('EnneagramCode', SET_NULL, null=True, blank=True)
    order_number = models.IntegerField(default=0)
    test_taken_date = models.DateField(blank=True, null=True)
    result_1 = models.IntegerField(default=0)
    score_1 = models.IntegerField(default=0)
    result_2 = models.IntegerField(default=0)
    score_2 = models.IntegerField(default=0)
    result_3 = models.IntegerField(default=0)
    score_3 = models.IntegerField(default=0)
    fullname = models.CharField(max_length=125, blank=True, null=True)
    email = models.CharField(max_length=125, blank=True, null=True)
    mobile = models.CharField(max_length=10, blank=True, null=True)
    testing = models.IntegerField(default=0)

    @property
    def invited_by_name(self):
        if self.invited_by:
            return self.invited_by.rep_fullname
        else:
            return ''

    @property
    def invited_date_formatted(self):
        if self.invited:
            return self.invited.strftime("%A, %B %d, %Y")  # Example: "Monday, March 17, 2025"
        return ""

    @property
    def enneagram_titles(self):
        enneagram_names = {
            1: 'Reformer',
            2: 'Helper',
            3: 'Achiever',
            4: 'Individualist',
            5: 'Investigator',
            6: 'Loyalist',
            7: 'Enthusiast',
            8: 'Challenger',
            9: 'Peacemaker',
        }

        results = [
            self.result_1,
            self.result_2,
            self.result_3,
        ]

        # Filter out 0s and map to titles
        titles = [
            f"{enneagram_names.get(num)} ({num})"
            for num in results
            if num > 0 and num in enneagram_names
        ]

        return ', '.join(titles) if titles else ''

class EnneagramCode(models.Model):
    expiration = models.DateTimeField(blank=False, null=False)
    status = models.IntegerField(choices=[
        (0, 'open'),
        (1, 'checked_out'),
        (2, 'expired'),
        (3, 'complete'),
    ], default=0)
    code = models.CharField(max_length=64, blank=False, null=False, unique=True)

    def __str__(self):
        return "%s - %s" % (self.code, self.status)


class QuickBooksToken(models.Model):
    company_id = models.CharField(max_length=50, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QBO Token for Company ID {self.company_id}"


class JournalEntry(models.Model):
    journal_id = models.CharField(max_length=20, unique=True)
    date = models.DateField()
    reference = models.TextField(blank=True, null=True)
    posted_to_qbo = models.BooleanField(default=False)
    qbo_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"JournalEntry {self.journal_id} ({'Posted' if self.posted_to_qbo else 'Pending'})"


class CallRailCall(models.Model):
    number_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    call_date_time = models.DateTimeField()
    duration = models.IntegerField(default=0)
    call_source = models.CharField(max_length=255, blank=True, null=True)
    call_keywords = models.TextField(blank=True, null=True)
    call_referrer = models.TextField(blank=True, null=True)
    call_medium = models.CharField(max_length=255, blank=True, null=True)
    call_landing_page = models.TextField(blank=True, null=True)
    call_campaign = models.CharField(max_length=255, blank=True, null=True)
    call_utm_content = models.CharField(max_length=255, blank=True, null=True)
    call_recording = models.URLField(blank=True, null=True)
    call_transcription = models.TextField(blank=True, null=True)
    call_agent_speaker_percent = models.FloatField(default=0.0)
    call_customer_speaker_percent = models.FloatField(default=0.0)
    call_sentiment = models.CharField(max_length=50, blank=True, null=True)
    prior_calls = models.IntegerField(default=0)
    gclid = models.CharField(max_length=255, blank=True, null=True)
    call_summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.phone_number} - {self.call_date_time}"