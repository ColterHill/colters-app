import json
import time
import msal
import requests
import csv
import logging
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Send spam warning emails to contacts. Use --test for single email test or --csv/--emails for bulk send.'

    def add_arguments(self, parser):
        # Test mode
        parser.add_argument(
            '--test',
            type=str,
            help='Send test email to specified email address',
        )
        
        # Bulk modes
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to CSV file containing email addresses',
        )
        
        parser.add_argument(
            '--emails',
            nargs='+',
            help='List of email addresses to send to (space separated)',
        )
        
        # Sender email (optional)
        parser.add_argument(
            '--sender',
            type=str,
            default='bbrooke@rmfp.com',
            help='Email address to send from (default: bbrooke@rmfp.com)',
        )
        
        # Dry run mode
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        self.setup_logging()
        
        sender_email = options['sender']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No emails will be sent')
            )
        
        # Validate that exactly one mode is specified
        modes = [options['test'], options['csv'], options['emails']]
        active_modes = [mode for mode in modes if mode is not None]
        
        if len(active_modes) != 1:
            raise CommandError(
                'You must specify exactly one mode: --test, --csv, or --emails'
            )
        
        # Execute the appropriate mode
        if options['test']:
            self.send_test_email(options['test'], sender_email, dry_run)
        elif options['csv']:
            self.send_bulk_from_csv(options['csv'], sender_email, dry_run)
        elif options['emails']:
            self.send_bulk_from_list(options['emails'], sender_email, dry_run)

    def setup_logging(self):
        """Set up logging for email operations."""
        log_filename = f'spam_warning_emails_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.stdout.write(f"Logging to: {log_filename}")

    def send_email_via_graph(self, sender_email, recipient_email, subject, body, body_type="Text"):
        """
        Sends an email using Microsoft Graph API.
        """
        # Load Graph API credentials
        client_id = "3a6abd6c-cdb2-4842-ae99-c783125b0323"
        client_secret = "No98Q~etn-_61PbGjh9BwO1DOWYP6oNsvlLCbaQc"
        tenant_id = "0a5c9006-73ed-4aed-8eca-9e3b83b2867b"

        if not all([client_id, client_secret, tenant_id]):
            raise ValueError("Missing one or more Graph API credentials")

        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scope = ["https://graph.microsoft.com/.default"]

        # Authenticate using MSAL
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret,
        )
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            raise Exception("Could not acquire access token: " + json.dumps(result, indent=2))
        access_token = result["access_token"]

        # Build the message payload
        message_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": body_type,
                    "content": body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient_email,
                        }
                    }
                ],
            },
            "saveToSentItems": "true"
        }

        # Graph API sendMail endpoint
        url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, data=json.dumps(message_payload))
            if response.status_code == 202:
                return True
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    retry_after = int(retry_after) if retry_after is not None else 10
                except ValueError:
                    retry_after = 10
                time.sleep(retry_after * (attempt + 1))
            else:
                raise Exception(f"Failed to send email. Status code: {response.status_code}. Response: {response.text}")

        raise Exception(f"Failed to send email after {max_retries} attempts. Last response: {response.text}")

    def get_email_template(self):
        """Return the spam warning email template."""
        subject = "IMPORTANT: Please Disregard Previous Email - Security Notice"
        
        body = """Hello,

We are writing to inform you that an email sent from our domain earlier this morning was identified as spam and should be disregarded immediately.

PLEASE DO NOT:
- Click any links in the previous email
- Download any attachments
- Respond to the suspicious email
- Provide any personal or sensitive information

Our IT security team has been notified and is taking appropriate action to secure our email systems.

If you have already interacted with the suspicious email, please:
1. Run a security scan on your device
2. Change any passwords you may have entered
3. Monitor your accounts for unusual activity

If you recieve future emails from this address that seem suspicious in any way, please disregard them.

We sincerely apologize for any inconvenience this may have caused and appreciate your understanding as we work to maintain the security of our communications.

If you have any questions or concerns, please contact us directly through our official channels.

Best regards,
RMFP Security Team"""

        return subject, body

    def send_test_email(self, test_email, sender_email, dry_run=False):
        """Send a test email to a single recipient."""
        self.stdout.write(
            self.style.SUCCESS(f'TEST MODE: Sending to {test_email}')
        )
        
        subject, body = self.get_email_template()
        
        if dry_run:
            self.stdout.write("DRY RUN - Would send:")
            self.stdout.write(f"From: {sender_email}")
            self.stdout.write(f"To: {test_email}")
            self.stdout.write(f"Subject: {subject}")
            self.stdout.write("Body preview: " + body[:100] + "...")
            return
        
        try:
            self.logger.info(f"Sending test email to {test_email}")
            
            self.send_email_via_graph(
                sender_email=sender_email,
                recipient_email=test_email,
                subject=subject,
                body=body,
                body_type="Text"
            )
            
            self.logger.info(f"✓ Test email successfully sent to {test_email}")
            self.stdout.write(
                self.style.SUCCESS(f"✓ Test email sent successfully to {test_email}")
            )
            self.stdout.write("\nPlease check your inbox and verify:")
            self.stdout.write("1. Email was received")
            self.stdout.write("2. Subject line is correct")
            self.stdout.write("3. Message content looks good")
            self.stdout.write(f"4. Sender shows as {sender_email}")
            self.stdout.write("\nIf everything looks good, you can proceed with bulk send!")
            
        except Exception as e:
            self.logger.error(f"✗ Failed to send test email to {test_email}: {e}")
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to send test email: {e}")
            )
            raise CommandError(f"Test email failed: {e}")

    def send_bulk_from_csv(self, csv_file_path, sender_email, dry_run=False):
        """Send bulk emails from CSV file."""
        self.stdout.write(
            self.style.SUCCESS(f'BULK MODE: Reading from CSV file {csv_file_path}')
        )
        
        # Read email addresses from CSV
        email_addresses = []
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect if there's a header and what the email column is called
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                has_header = sniffer.has_header(sample)
                
                reader = csv.reader(csvfile)
                if has_header:
                    headers = next(reader)
                    self.logger.info(f"CSV headers detected: {headers}")
                    self.stdout.write(f"CSV headers: {headers}")
                    
                    # Find email column (look for common email column names)
                    email_col_index = 0
                    for i, header in enumerate(headers):
                        if any(keyword in header.lower() for keyword in ['email', 'mail', 'address']):
                            email_col_index = i
                            self.logger.info(f"Using column '{header}' for email addresses")
                            self.stdout.write(f"Using column '{header}' for emails")
                            break
                else:
                    email_col_index = 0
                    self.logger.info("No header detected, using first column for emails")
                    self.stdout.write("No header detected, using first column")
                
                for row_num, row in enumerate(reader, start=2 if has_header else 1):
                    if row and len(row) > email_col_index:
                        email = row[email_col_index].strip()
                        if email and '@' in email:  # Basic email validation
                            email_addresses.append(email)
                        else:
                            self.logger.warning(f"Invalid email in row {row_num}: {email}")
                            
        except FileNotFoundError:
            raise CommandError(f"CSV file not found: {csv_file_path}")
        except Exception as e:
            raise CommandError(f"Error reading CSV file: {e}")
        
        self.stdout.write(f"Found {len(email_addresses)} valid email addresses")
        self.send_bulk_emails(email_addresses, sender_email, dry_run)

    def send_bulk_from_list(self, email_list, sender_email, dry_run=False):
        """Send bulk emails from list of email addresses."""
        self.stdout.write(
            self.style.SUCCESS(f'BULK MODE: Sending to {len(email_list)} recipients')
        )
        
        # Basic email validation
        valid_emails = []
        for email in email_list:
            email = email.strip()
            if email and '@' in email:
                valid_emails.append(email)
            else:
                self.stdout.write(
                    self.style.WARNING(f"Skipping invalid email: {email}")
                )
        
        self.stdout.write(f"Found {len(valid_emails)} valid email addresses")
        self.send_bulk_emails(valid_emails, sender_email, dry_run)

    def send_bulk_emails(self, email_addresses, sender_email, dry_run=False):
        """Send emails to a list of recipients with rate limiting."""
        subject, body = self.get_email_template()
        
        if dry_run:
            self.stdout.write("DRY RUN - Would send to:")
            for i, email in enumerate(email_addresses[:10]):  # Show first 10
                self.stdout.write(f"  {i+1}. {email}")
            if len(email_addresses) > 10:
                self.stdout.write(f"  ... and {len(email_addresses) - 10} more")
            self.stdout.write(f"\nFrom: {sender_email}")
            self.stdout.write(f"Subject: {subject}")
            return
        
        self.logger.info(f"Starting bulk email send to {len(email_addresses)} recipients")
        
        successful_sends = 0
        failed_sends = 0
        
        for i, recipient_email in enumerate(email_addresses, 1):
            try:
                self.stdout.write(f"Sending {i}/{len(email_addresses)} to {recipient_email}")
                self.logger.info(f"Sending email {i}/{len(email_addresses)} to {recipient_email}")
                
                self.send_email_via_graph(
                    sender_email=sender_email,
                    recipient_email=recipient_email,
                    subject=subject,
                    body=body,
                    body_type="Text"
                )
                
                successful_sends += 1
                self.logger.info(f"✓ Successfully sent to {recipient_email}")
                
                # Rate limiting: wait between sends to avoid hitting API limits
                if i % 10 == 0:  # Every 10 emails, wait a bit longer
                    self.logger.info("Pausing for rate limiting...")
                    self.stdout.write("Pausing for rate limiting...")
                    time.sleep(2)
                else:
                    time.sleep(0.5)  # Small delay between each email
                    
            except Exception as e:
                failed_sends += 1
                self.logger.error(f"✗ Failed to send to {recipient_email}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to send to {recipient_email}: {e}")
                )
                
                # If we hit rate limits, wait longer
                if "429" in str(e) or "rate" in str(e).lower():
                    self.logger.info("Rate limit detected, waiting 30 seconds...")
                    self.stdout.write("Rate limit detected, waiting 30 seconds...")
                    time.sleep(30)
        
        # Summary
        success_rate = (successful_sends/len(email_addresses)*100) if email_addresses else 0
        summary = f"""
BULK EMAIL SUMMARY:
==================
Total emails processed: {len(email_addresses)}
Successful sends: {successful_sends}
Failed sends: {failed_sends}
Success rate: {success_rate:.1f}%
        """
        
        self.logger.info(summary)
        self.stdout.write(self.style.SUCCESS(summary))
