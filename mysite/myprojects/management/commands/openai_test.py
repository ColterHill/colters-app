from django.core.management.base import BaseCommand
import openai
from openai import OpenAI
import base64


API_KEY = "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"
openai.api_key = API_KEY

class Command(BaseCommand):
    def handle(self, *args, **options):
        # response = openai.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {
        #             "role": "user",
        #             "content": "Write a recipe for spaghetti."
        #         }
        #     ]
        # )

        # print(response.choices[0].message)

        completion = openai.chat.completions.create(
            model="gpt-4o-audio-preview",
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "wav"},
            messages=[
                {
                    "role": "user",
                    "content": "Is a golden retriever a good family dog?"
                }
            ]
        )

        print(completion.choices[0])

        wav_bytes = base64.b64decode(completion.choices[0].message.audio.data)
        with open("dog.wav", "wb") as f:
            f.write(wav_bytes)