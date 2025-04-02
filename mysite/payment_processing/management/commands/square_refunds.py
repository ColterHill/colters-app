from django.core.management.base import BaseCommand
from square.http.auth.o_auth_2 import BearerAuthCredentials
from payment_processing.models import PaymentTransactions
from square.client import Client
import uuid

sandbox_token = 'EAAAl51Ah6ogt8nrKM0C-ldw4f_fERzC91gkQXqx82xv5et97YDjuP73ECG_xayH'
production_token = 'EAAAl-HYUYo9dYxZZoqW_3CsrUAu8tQSJ5RB6BI5zwpfOtKACwQ7wqwgbstBU0N7'

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
        UUID_STRING = str(uuid.uuid4())

        payment_info = client.payments.list_payments()
        payments = payment_info.body.get('payments', [])
        for payment in payments:
            payment_id = payment['id']
            amount_money = payment['amount_money']
            amount = amount_money['amount']

            print(f"ID : {payment_id}, Amount: {amount}")

        # refund_payment = client.refunds.refund_payment(
        #     body = {
        #         "idempotency_key": UUID_STRING,
        #         "amount_money": {
        #         "amount": 3500,
        #         "currency": "USD"
        #         },
        #         "payment_id": "L3B4Q9ICVFvQBpeS1v4Ct1EKL8WZY",
        #         "reason": "Example"
        #     }
        # )

        # if refund_payment.is_success():
        #     print(refund_payment.body)
        # elif refund_payment.is_error():
        #     print(refund_payment.errors)