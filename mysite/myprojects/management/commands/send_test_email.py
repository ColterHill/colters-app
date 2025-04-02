# myapp/management/commands/send_test_email_graph.py

import json
import requests
import msal
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Sends a test email using Microsoft Graph API"

    def handle(self, *args, **kwargs):
        # Configuration - Replace these with your actual values or load from environment variables.
        client_id = "3a6abd6c-cdb2-4842-ae99-c783125b0323"
        client_secret = "No98Q~etn-_61PbGjh9BwO1DOWYP6oNsvlLCbaQc"
        tenant_id = "0a5c9006-73ed-4aed-8eca-9e3b83b2867b"
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scope = ["https://graph.microsoft.com/.default"]

        # Email details
        sender_email = "wtirado@rmfp.com"
        recipient_email = "bbrooke@rmfp.com"
        cc_recipient_email = "chill@rmfp.com"
        email_subject = "Test Email from Microsoft Graph API"
        email_body = "This is a test email sent using Microsoft Graph API from Django."

        # Initialize MSAL confidential client
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret,
        )

        # Acquire an access token
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            self.stdout.write(self.style.ERROR("Could not acquire access token."))
            self.stdout.write(self.style.ERROR(json.dumps(result, indent=2)))
            return

        access_token = result["access_token"]

        # Construct the email payload
        message = {
            "message": {
                "subject": email_subject,
                "body": {
                    "contentType": "Text",
                    "content": email_body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient_email,
                        }
                    }
                ],
                "ccRecipients": [
                    {
                        "emailAddress": {
                            "address": cc_recipient_email,
                        }
                    },
                ],
            },
            "saveToSentItems": "true"
        }

        # Send email via Microsoft Graph API
        url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, data=json.dumps(message))

        if response.status_code == 202:
            self.stdout.write(self.style.SUCCESS("Email sent successfully."))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to send email. Status code: {response.status_code}."))
            self.stdout.write(self.style.ERROR(f"Response: {response.text}"))
