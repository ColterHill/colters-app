import json
import time
import msal
import requests
import csv
import logging
from datetime import datetime


def send_email_via_graph(
        sender_email,
        recipient_email,
        subject,
        body,
        cc_recipients=None,
        bcc_recipients=None,
        body_type="Text"  # Accepts "Text" or "HTML"
):
    """
    Sends an email using Microsoft Graph API.

    :param sender_email: The email address to send from (must have send-mail permissions)
    :param recipient_email: The primary recipient's email address (string)
    :param subject: Email subject line
    :param body: Email body content (HTML or plain text)
    :param cc_recipients: Optional; a list of email addresses to CC or a single email address string
    :param bcc_recipients: Optional; a list of email addresses to BCC or a single email address string
    :param body_type: Optional; "Text" or "HTML", defaults to "Text"
    :return: True if email sent successfully; raises an Exception otherwise.
    """

    # Load Graph API credentials (ideally use environment variables instead of hardcoding)
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
                "contentType": body_type,  # "Text" or "HTML"
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

    # Add CC recipients if provided
    if cc_recipients:
        if isinstance(cc_recipients, str):
            cc_recipients = [cc_recipients]
        message_payload["message"]["ccRecipients"] = [
            {"emailAddress": {"address": cc}} for cc in cc_recipients
        ]

    # Add BCC recipients if provided
    if bcc_recipients:
        if isinstance(bcc_recipients, str):
            bcc_recipients = [bcc_recipients]
        message_payload["message"]["bccRecipients"] = [
            {"emailAddress": {"address": bcc}} for bcc in bcc_recipients
        ]

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


def setup_logging():
    """Set up logging for bulk email operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'bulk_email_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def send_bulk_spam_warning_emails(csv_file_path, sender_email="bbrooke@rmfp.com"):
    """
    Send spam warning emails to a list of recipients from a CSV file.
    
    :param csv_file_path: Path to CSV file containing email addresses
    :param sender_email: Email address to send from (defaults to bbrooke@rmfp.com)
    """
    logger = setup_logging()
    
    # Email template for spam warning
    subject = "IMPORTANT: Please Disregard Previous Email - Security Notice"
    
    body = """Dear Valued Contact,

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

We sincerely apologize for any inconvenience this may have caused and appreciate your understanding as we work to maintain the security of our communications.

If you have any questions or concerns, please contact us directly through our official channels.

Best regards,
RMFP Security Team"""

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
                logger.info(f"CSV headers detected: {headers}")
                # Find email column (look for common email column names)
                email_col_index = 0
                for i, header in enumerate(headers):
                    if any(keyword in header.lower() for keyword in ['email', 'mail', 'address']):
                        email_col_index = i
                        logger.info(f"Using column '{header}' for email addresses")
                        break
            else:
                email_col_index = 0
                logger.info("No header detected, using first column for emails")
            
            for row_num, row in enumerate(reader, start=2 if has_header else 1):
                if row and len(row) > email_col_index:
                    email = row[email_col_index].strip()
                    if email and '@' in email:  # Basic email validation
                        email_addresses.append(email)
                    else:
                        logger.warning(f"Invalid email in row {row_num}: {email}")
                        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file_path}")
        return
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return
    
    logger.info(f"Found {len(email_addresses)} valid email addresses")
    
    # Send emails with rate limiting
    successful_sends = 0
    failed_sends = 0
    
    for i, recipient_email in enumerate(email_addresses, 1):
        try:
            logger.info(f"Sending email {i}/{len(email_addresses)} to {recipient_email}")
            
            send_email_via_graph(
                sender_email=sender_email,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                body_type="Text"
            )
            
            successful_sends += 1
            logger.info(f"✓ Successfully sent to {recipient_email}")
            
            # Rate limiting: wait between sends to avoid hitting API limits
            if i % 10 == 0:  # Every 10 emails, wait a bit longer
                logger.info("Pausing for rate limiting...")
                time.sleep(2)
            else:
                time.sleep(0.5)  # Small delay between each email
                
        except Exception as e:
            failed_sends += 1
            logger.error(f"✗ Failed to send to {recipient_email}: {e}")
            
            # If we hit rate limits, wait longer
            if "429" in str(e) or "rate" in str(e).lower():
                logger.info("Rate limit detected, waiting 30 seconds...")
                time.sleep(30)
    
    # Summary
    logger.info(f"""
    
BULK EMAIL SUMMARY:
==================
Total emails processed: {len(email_addresses)}
Successful sends: {successful_sends}
Failed sends: {failed_sends}
Success rate: {(successful_sends/len(email_addresses)*100):.1f}%
    """)


def send_bulk_emails_from_list(email_list, sender_email="bbrooke@rmfp.com"):
    """
    Alternative function to send emails from a Python list instead of CSV.
    
    :param email_list: List of email addresses as strings
    :param sender_email: Email address to send from
    """
    logger = setup_logging()
    
    # Same email template
    subject = "IMPORTANT: Please Disregard Previous Email - Security Notice"
    
    body = """Dear Valued Contact,

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

We sincerely apologize for any inconvenience this may have caused and appreciate your understanding as we work to maintain the security of our communications.

If you have any questions or concerns, please contact us directly through our official channels.

Best regards,
RMFP Security Team"""

    logger.info(f"Starting bulk email send to {len(email_list)} recipients")
    
    successful_sends = 0
    failed_sends = 0
    
    for i, recipient_email in enumerate(email_list, 1):
        try:
            logger.info(f"Sending email {i}/{len(email_list)} to {recipient_email}")
            
            send_email_via_graph(
                sender_email=sender_email,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                body_type="Text"
            )
            
            successful_sends += 1
            logger.info(f"✓ Successfully sent to {recipient_email}")
            
            # Rate limiting
            if i % 10 == 0:
                logger.info("Pausing for rate limiting...")
                time.sleep(2)
            else:
                time.sleep(0.5)
                
        except Exception as e:
            failed_sends += 1
            logger.error(f"✗ Failed to send to {recipient_email}: {e}")
            
            if "429" in str(e) or "rate" in str(e).lower():
                logger.info("Rate limit detected, waiting 30 seconds...")
                time.sleep(30)
    
    logger.info(f"""
    
BULK EMAIL SUMMARY:
==================
Total emails processed: {len(email_list)}
Successful sends: {successful_sends}
Failed sends: {failed_sends}
Success rate: {(successful_sends/len(email_list)*100):.1f}%
    """)


def send_test_email(test_email, sender_email="bbrooke@rmfp.com"):
    """
    Send a test spam warning email to a single recipient.
    
    :param test_email: Email address to send the test to
    :param sender_email: Email address to send from
    """
    logger = setup_logging()
    
    subject = "IMPORTANT: Please Disregard Previous Email - Security Notice"
    
    body = """Dear Valued Contact,

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

We sincerely apologize for any inconvenience this may have caused and appreciate your understanding as we work to maintain the security of our communications.

If you have any questions or concerns, please contact us directly through our official channels.

Best regards,
RMFP Security Team"""

    try:
        logger.info(f"Sending test email to {test_email}")
        
        send_email_via_graph(
            sender_email=sender_email,
            recipient_email=test_email,
            subject=subject,
            body=body,
            body_type="Text"
        )
        
        logger.info(f"✓ Test email successfully sent to {test_email}")
        print(f"\n🎉 SUCCESS! Test email sent to {test_email}")
        print("\nPlease check your inbox and verify:")
        print("1. Email was received")
        print("2. Subject line is correct")
        print("3. Message content looks good")
        print("4. Sender shows as bbrooke@rmfp.com")
        print("\nIf everything looks good, you can proceed with the bulk send!")
        
    except Exception as e:
        logger.error(f"✗ Failed to send test email to {test_email}: {e}")
        print(f"\n❌ ERROR: Could not send test email")
        print(f"Error details: {e}")
        print("\nPlease check your credentials and try again.")


if __name__ == "__main__":
    # STEP 1: Test with a single email first (RECOMMENDED)
    # Replace with your email address to test
    send_test_email("your.email@domain.com")
    
    # STEP 2: After testing, uncomment ONE of the options below:
    
    # Option 1: Use CSV file for bulk send
    # send_bulk_spam_warning_emails("contacts.csv")
    
    # Option 2: Use Python list for bulk send
    # email_list = [
    #     "contact1@example.com",
    #     "contact2@example.com",
    #     # ... add more emails
    # ]
    # send_bulk_emails_from_list(email_list)
    
    print("\n" + "="*50)
    print("BULK EMAIL SCRIPT READY!")
    print("="*50)
    print("\nCURRENT MODE: Test single email")
    print("\nTo use:")
    print("1. FIRST: Edit the send_test_email line above with your email")
    print("2. Run the script to test")
    print("3. THEN: Comment out the test line and uncomment bulk option")
    print("\nBulk options:")
    print("- CSV file: send_bulk_spam_warning_emails('your_contacts.csv')")
    print("- Email list: send_bulk_emails_from_list([email_list])")