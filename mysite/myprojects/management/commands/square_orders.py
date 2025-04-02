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
        
        result = client.orders.create_order(
        body = {
            "order": {
            "location_id": "LD6MKAX2FKMTY",
            "line_items": [
                {
                "name": "Hamburger",
                "quantity": "1",
                "modifiers": [
                    {
                    "name": "cheese",
                    "quantity": "2",
                    "base_price_money": {
                        "amount": 50,
                        "currency": "USD"
                    }
                    }
                ],
                "base_price_money": {
                    "amount": 1200,
                    "currency": "USD"
                }
                }
            ]
            },
            "fulfillments": [
                {
                "type": "PICKUP",
                "state": "PROPOSED",
                "pickup_details": {
                    "recipient": {
                    "display_name": "Jaiden Urie"
                    },
                    "expires_at": "2024-10-14T20:21:54.859Z",
                    "auto_complete_duration": "P0DT1H0S",
                    "schedule_type": "SCHEDULED",
                    "pickup_at": "2024-10-14T19:21:54.859Z",
                    "note": "Pour over coffee"
                }
                }
            ],
            "idempotency_key": "7fff5e38-5da5-4fd2-a00d-39a6f289af58"
        }
        )

        if result.is_success():
            print(result.body)
        elif result.is_error():
            print(result.errors)