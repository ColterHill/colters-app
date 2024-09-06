from django.core.management.base import BaseCommand
from square.http.auth.o_auth_2 import BearerAuthCredentials
from square.client import Client

sandbox_token = 'EAAAl51Ah6ogt8nrKM0C-ldw4f_fERzC91gkQXqx82xv5et97YDjuP73ECG_xayH'
production_token = 'EAAAl-HYUYo9dYxZZoqW_3CsrUAu8tQSJ5RB6BI5zwpfOtKACwQ7wqwgbstBU0N7'

payouts_api = Client(
    bearer_auth_credentials=BearerAuthCredentials(
        access_token=sandbox_token
    ),
    environment='sandbox').payouts
# client = Client(
#     bearer_auth_credentials=BearerAuthCredentials(
#         access_token=production_token
#     ),
#     environment='production')



class Command(BaseCommand):
    def handle(self, *args, **options):
        result = payouts_api.list_payouts()
        if result.is_success():
            payouts = result.body.get('payouts', [])
            for payout in payouts:
                print("Created Date:", payout['created_at'], "Scheduled Date:", payout['arrival_date'], "Payout ID:", payout['id'], "Amount:", payout['amount_money']['amount'])
        elif result.is_error():
            print("Error retrieving payouts: ", result.errors)