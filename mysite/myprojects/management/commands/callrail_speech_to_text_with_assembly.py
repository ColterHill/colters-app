from django.core.management.base import BaseCommand
from myprojects.models import PhoneCalls
import requests
import assemblyai as aai



class Command(BaseCommand):
    def handle(self, *args, **options):
        # CallRail API Key
        API_KEY = "477ac881b043df62d5b0d7104db1fbd2"
        ACCOUNT_ID = "227527750"

        url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/calls.json?fields=tracking_phone_number,customer_phone_number,recording_player,recording_duration,start_time,transcription,sentiment"

        # AssemblyAI Key
        aai.settings.api_key = "ae8d26aa656741e3a94f1b2bbe4c1f04"
        transcriber = aai.Transcriber()

        # Headers
        headers = {
            "Authorization": f"Token token={API_KEY}",
            "Content-Type": "application/json"
        }

        # Get tracking number data
        # trackers = []
        # tracker_url  = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/trackers.json"
        # tracker_response = response = requests.get(tracker_url, headers=headers)

        # t_data = tracker_response.json()
        # trackers.extend(t_data['trackers'])

        # tracker_data = t_data['trackers']

        # result_array = []

        # for tracker in tracker_data:
        #     tracker_name = tracker['name']
        #     tracker_numbers = tracker['tracking_numbers']

        #     if tracker_numbers:
        #         for number in tracker_numbers:
        #             result_array.append({
        #                 "tracking_name": tracker_name,
        #                 "tracking_number": number
        #             })
        # print(result_array)

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
                customer_number = call['customer_phone_number']
                call_recording = call['recording_player']
                call_duration = call['recording_duration']
                call_date = call['start_time']
                transcription = call['transcription']
                sentiment = call['sentiment']

                

                if call_recording and call_duration > 20 and call_recording != None:
                    corrected_recording_url = call_recording.replace("/recording", "/recording/redirect")
                    print(f"CALL DATE: {call_date} CUSTOMER #: {customer_number}, TRACKING #: {tracking_number}, DURATION: {call_duration}")
                    print(f"RECORDING: {corrected_recording_url}")
                    print(f"TRANSCRIPTION: {transcription}")
                    print(f"SENTIMENT: {sentiment}")
                    print()
                    

                    # FILE_URL = corrected_recording_url

                    # config = aai.TranscriptionConfig(speaker_labels=True)

                    
                    # transcript = transcriber.transcribe(FILE_URL, config=config)

                    
                    # if transcript.status == aai.TranscriptStatus.error:
                    #     print(f"Transcription failed: {transcript.error}")
                        
                    # else:
                    #     # print(transcript.text)
                    #     print("It didn't error")

                    #     transcription_text =[]
                    #     if transcript.utterances:
                    #         for utterance in transcript.utterances:
                    #             # print(f"Speaker {utterance.speaker}: {utterance.text}")
                    #             transcription_text.append(f"Speaker {utterance.speaker}: {utterance.text}")

                    #         conversation_str = "\n".join(transcription_text)
                    #         print(conversation_str)
                    #         print()
                    #         row_count += 1
                            # if row_count > :
                            #     break
                    

        #             # Add to DB
        #             phone_call, is_new = PhoneCalls.objects.get_or_create(customer_number=customer_number, call_date=call_date, duration=call_duration)
                
        #             if is_new:
        #                 phone_call.tracking_number = tracking_number
        #                 phone_call.recording_url = corrected_recording_url
        #                 phone_call.transcription = transcription_text
        #                 phone_call.save(update_fields=['tracking_number', 'recording_url', 'transcription'])

        #     print(row_count)