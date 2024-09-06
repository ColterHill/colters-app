from django.core.management.base import BaseCommand
from square.http.auth.o_auth_2 import BearerAuthCredentials
from square.client import Client

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
        result = client.payments.list_payments(
            # begin_time = "2023-03-01T22:23:55.737Z",
            # cursor = "XlKamNtVmhkR1ZrUVhR_SW1sa0lqb2mRsVkhXVEF4YkRkSU5ITk9XbGtpZlE",
            # location_id = "VJN4XSBFTVPK9",
            # card_brand = "VISA",
            limit = 10
            )
        payments = result.body["payments"]
        # payment_id = payments[0]['id']
        # payment_type = payments[0]['source_type']
        if result.is_success():
            for object in payments:
                print(object)
                payment_id = object['id']
                payment_type = object['source_type']
                # if object['card_details']:
                #     card_details = object['card_details']
                # else:
                #     continue

                print(payment_id)
                print(payment_type)
            # print(payment_id)
            # print(payment_type)
        elif result.is_error():
            print(result.errors)