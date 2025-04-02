# `pip3 install assemblyai` (macOS)
# `pip install assemblyai` (Windows)

import assemblyai as aai

aai.settings.api_key = "ae8d26aa656741e3a94f1b2bbe4c1f04"
transcriber = aai.Transcriber()

from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    def handle(self, *args, **options):
        # FILE_URL = "https://app.callrail.com/calls/CALd8a8f75ed674484b8ad6ad2cb5f393db/recording/redirect?access_key=c4f2ed572200bb21980f"
        FILE_URL = 'https://app.callrail.com/calls/CALb28b5b08f0b94aabac3bf2427892bac1/recording/redirect?access_key=c6aedd245f718d3de815'

        # You can also transcribe a local file by passing in a file path
        # FILE_URL = './path/to/file.mp3'

        config = aai.TranscriptionConfig(speaker_labels=True)

        transcript = transcriber.transcribe(FILE_URL, config)

        if transcript.status == aai.TranscriptStatus.error:
            print(f"Transcription failed: {transcript.error}")
            
        else:
            print(transcript.text)

            for utterance in transcript.utterances:
                print(f"Speaker {utterance.speaker}: {utterance.text}")