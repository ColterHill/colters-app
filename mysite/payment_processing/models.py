from django.db import models

# Create your models here.

class PaymentTransactions(models.Model):
    location_id = models.CharField(null=True, blank=True, max_length=64)
    created_date = models.DateTimeField()
    payout_scheduled_date = models.DateTimeField()
    payment_id = models.CharField(null=True, blank=True, max_length=64)
    payout_id = models.CharField(null=True, blank=True, max_length=64)
    payout_entry_id = models.CharField(null=True, blank=True, max_length=64)
    amount = models.DecimalField(default=0, max_digits=9, decimal_places=4)
    transaction_type = models.CharField(null=True, blank=True, max_length=64)
    transaction_source_type = models.CharField(null=True, blank=True, max_length=64)
    card_brand = models.CharField(null=True, blank=True, max_length=64)
    