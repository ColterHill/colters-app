from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Your API Key
        API_KEY = "477ac881b043df62d5b0d7104db1fbd2"
        ACCOUNT_ID = "227527750"

        url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/calls.json"

        # Headers
        headers = {
            "Authorization": f"Token token={API_KEY}",
            "Content-Type": "application/json"
        }

        # Make the API Request
        # response = requests.get(url, headers=headers)


        # Check and Display Response
        row_count = 0
        # if response.status_code == 200:
        #     calls = response.json()
        #     print("Calls List:")
        #     print(calls['page'])
        #     print(calls['total_pages'])
        #     print(calls['total_records'])
        #     for call in calls['calls']:
        #         # customer_number = call['customer_phone_number']
        #         # number_called = call['tracking_phone_number']
        #         # call_recording = call['recording_player']
        #         # call_duration = call['duration']
        #         # tracking_number = call['tracking_phone_number']
        #         # if tracking_number == '+17207121475':
        #         #     print(f"Customer Number: {customer_number}, Number Called: {number_called}, Recording: {call_recording}")
        #         #     print(call)
        #         row_count += 1
        #     print(row_count)
        # else:
        #     print(f"Error {response.status_code}: {response.text}")

         # Pagination Variables
        calls = []
        page = 1
        per_page = 250  # Max number of records per page
        total_calls = 0

        params = {"page": page, "per_page": per_page,"start_date": "2024-01-01", "end_date": "2024-12-31"}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            calls.extend(data['calls'])
            total_calls += len(data['calls'])

            call_data = data['calls']

            for call in call_data:
                customer_number = call['customer_phone_number']
                number_called = call['tracking_phone_number']
                call_recording = call['recording_player']
                call_duration = call['duration']
                tracking_number = call['tracking_phone_number']
                call_date = call['start_time']

                if call_recording:
                    print(f"CALL DATE: {call_date} CUSTOMER #: {customer_number}, TRACKING #: {tracking_number}")
                    print(call)
                    print()
                    print()
                    row_count += 1
                    if row_count > 3:
                        break