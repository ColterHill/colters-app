from django.core.management.base import BaseCommand
from myprojects.models import PhoneCalls
import requests
import assemblyai as aai
import re



class Command(BaseCommand):
    def handle(self, *args, **options):
        # CallRail API Key
        API_KEY = "477ac881b043df62d5b0d7104db1fbd2"
        ACCOUNT_ID = "227527750"

        # GET URL with correct fields
        url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/calls.json?fields=tracking_phone_number,customer_phone_number,recording_player,recording_duration,start_time,transcription,sentiment"

        # Headers
        headers = {
            "Authorization": f"Token token={API_KEY}",
            "Content-Type": "application/json"
        }

        # Get tracking number data
        trackers = []
        tracker_url  = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/trackers.json"
        page = 1
        per_page = 250  # Max number of records per page
        params = {"active": "true", "page": page, "per_page": per_page}
        tracker_response = response = requests.get(tracker_url, headers=headers, params=params)

        t_data = tracker_response.json()
        trackers.extend(t_data['trackers'])

        tracker_data = t_data['trackers']

        result_array = []

        for tracker in tracker_data:
            tracker_name = tracker['name']
            tracker_numbers = tracker['tracking_numbers']

            if tracker_numbers:
                for number in tracker_numbers:
                    result_array.append({
                        "tracking_name": tracker_name,
                        "tracking_number": number
                    })
       
        # print(result_array)
        tracker_lookup = {
            tracker["tracking_number"]: tracker["tracking_name"] for tracker in result_array
        }

        row_count = 0
    
        # Pagination Variables
        calls = []
        page = 1
        per_page = 250  # Max number of records per page
        total_calls = 0

        params = {"page": page, "per_page": per_page,"start_date": "2025-02-18"}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            calls.extend(data['calls'])
            total_calls += len(data['calls'])

            call_data = data['calls']

            for call in call_data:
                row_count += 1
                if row_count > 25:
                    break
                tracking_number = call['tracking_phone_number']
                tracking_number_name = tracker_lookup.get(tracking_number, 'No tracker found')
                customer_number = call['customer_phone_number']
                call_recording = call['recording_player']
                call_duration = call['recording_duration']
                call_date = call['start_time']
                transcription = call['transcription']
                sentiment = call['sentiment']
                if transcription is not None:
                    formatted_transcription = re.sub(r'\s*(Agent:|Caller:)', r'\n\1', transcription).strip()
                else:
                    formatted_transcription = ""

                if call_recording and call_duration > 20 and call_recording != None:
                    corrected_recording_url = call_recording.replace("/recording", "/recording/redirect")
                    print(f"CALL DATE: {call_date} CUSTOMER #: {customer_number}, TRACKING #: {tracking_number}, TRACKING NAME: {tracking_number_name}, DURATION: {call_duration}")
                    print(f"RECORDING: {corrected_recording_url}")
                    print(f"TRANSCRIPTION: {formatted_transcription}")
                    print(f"SENTIMENT: {sentiment}")
                    print()
            

        #             # Add to DB
                    phone_call, is_new = PhoneCalls.objects.get_or_create(customer_number=customer_number, call_date=call_date, duration=call_duration)
                
                    if is_new:
                        # phone_call.duration = call_duration
                        phone_call.tracking_number = tracking_number
                        phone_call.tracking_number_name = tracking_number_name
                        phone_call.recording_url = corrected_recording_url
                        phone_call.transcription = formatted_transcription
                        phone_call.sentiment = sentiment
                        phone_call.save(update_fields=['tracking_number', 'tracking_number_name', 'recording_url', 'transcription', 'sentiment'])

        #     print(row_count)