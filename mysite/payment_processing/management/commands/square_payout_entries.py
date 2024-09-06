from django.core.management.base import BaseCommand
from square.http.auth.o_auth_2 import BearerAuthCredentials
from payment_processing.models import PaymentTransactions
from square.client import Client

sandbox_token = 'Sanbox_Key'
production_token = 'Production_Key'

client = Client(
    bearer_auth_credentials=BearerAuthCredentials(
        access_token=sandbox_token
    ),
    environment='sandbox')
# client = Client(
#     bearer_auth_credentials=BearerAuthCredentials(
#         access_token=production_token
#     ),
#     environment='production')



class Command(BaseCommand):
    def handle(self, *args, **options):
        payout_info = client.payouts.list_payouts()
        payouts = payout_info.body.get('payouts', [])
        for payout in payouts:
            po_id = payout['id']
            
            payout_entry_info = client.payouts.list_payout_entries(payout_id = po_id)
            payout_entry = payout_entry_info.body.get('payout_entries', [])
            for entry in payout_entry:
                gross_amount_money = entry['gross_amount_money']
                type_charge_details = entry['type_charge_details']
                # print("Payment ID:", type_charge_details['payment_id'], "Type:", entry['type'], "Amount:", gross_amount_money['amount'])

                payment_info = client.payments.get_payment(payment_id = type_charge_details['payment_id'])
                payment = payment_info.body['payment']
                card_details = payment['card_details']
                card = card_details['card']

                payment_id = type_charge_details['payment_id']
                location_id = payment['location_id']
                created = payment['created_at']
                payout_scheduled_date = payout['arrival_date']
                payout_entry_id = entry['id']
                amount = gross_amount_money['amount'] / 100
                transaction_type = entry['type']
                transaction_source_type = payment['source_type']
                card_brand = card['card_brand']
                
                payment_transactions, is_new = PaymentTransactions.objects.get_or_create(payment_id=payment_id)

                if is_new:
                    PaymentTransactions.payout_id = po_id
                    PaymentTransactions.location_id = location_id
                    PaymentTransactions.created_date = created
                    PaymentTransactions.payout_scheduled_date = payout_scheduled_date
                    PaymentTransactions.payout_entry_id = payout_entry_id
                    PaymentTransactions.amount = amount
                    PaymentTransactions.transaction_type = transaction_type
                    PaymentTransactions.transaction_source_type = transaction_source_type
                    PaymentTransactions.card_brand = card_brand

                    payment_transactions.save(update_fields=['payout_id', 'location_id', 'created_date', 'payout_scheduled_date', 'payout_entry_id', 'amount', 'transaction_type', 'transaction_source_type', 'card_brand'])