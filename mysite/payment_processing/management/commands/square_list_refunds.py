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

        result = client.refunds.list_payment_refunds()

        if result.is_success():
            print(result.body)
        elif result.is_error():
            print(result.errors)