import csv
import os
import json
import requests
from datetime import datetime
from urllib.parse import quote
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from dotenv import load_dotenv
from myprojects.models import JournalEntry

def get_qbo_headers(content_type="application/json"):
    load_dotenv()
    token = os.getenv("QBO_ACCESS_TOKEN")
    if not token:
        raise Exception("❌ QBO_ACCESS_TOKEN is missing from .env")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": content_type,
    }

def get_company_id():
    load_dotenv()
    company_id = os.getenv("QBO_COMPANY_ID")
    if not company_id:
        raise Exception("❌ QBO_COMPANY_ID is missing from .env")
    return company_id

def parse_csv_date(date_str):
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%y")
        return dt.date().isoformat()
    except ValueError:
        raise ValueError(f"❌ Invalid date format: {date_str}. Expected MM/DD/YY.")

def get_qbo_account_map():
    query = "SELECT * FROM Account WHERE MetaData.LastUpdatedTime > '2014-01-01T00:00:00-00:00'"
    encoded_query = quote(query)
    company_id = get_company_id()
    url = f"https://quickbooks.api.intuit.com/v3/company/{company_id}/query?query={encoded_query}&minorversion=75"
    headers = get_qbo_headers(content_type="text/plain")

    print(f"🔍 QBO URL: {url}")
    print(f"🔐 Access token starts with: {headers['Authorization'][:20]}...")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch accounts: {response.status_code} {response.text}")

    accounts = response.json().get("QueryResponse", {}).get("Account", [])
    account_map = {}
    for account in accounts:
        acct_num = account.get("AcctNum")
        if acct_num:
            account_map[acct_num] = {
                "value": account["Id"],
                "name": account["Name"]
            }
    return account_map

class Command(BaseCommand):
    help = "Push grouped journal entries from CSV to QBO"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        self.stdout.write("🔄 Fetching account mapping from QBO...")
        try:
            account_map = get_qbo_account_map()
        except Exception as e:
            self.stderr.write(str(e))
            return

        self.stdout.write(f"✅ Fetched {len(account_map)} accounts.\n")

        # Group rows by journal entry number
        entries_by_journal = defaultdict(list)

        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

            for row in reader:
                row = {k.strip().lower(): v for k, v in row.items()}
                entries_by_journal[row["journal entry"]].append(row)

        # Process each journal entry group
        for journal_id, rows in entries_by_journal.items():
            if JournalEntry.objects.filter(journal_id=journal_id, posted_to_qbo=True).exists():
                self.stdout.write(self.style.WARNING(f"⚠️  Journal {journal_id} already posted. Skipping."))
                continue

            lines = []
            total_debit = 0.0
            total_credit = 0.0

            for row in rows:
                acct_num = row["account number"]
                account_info = account_map.get(acct_num)
                if not account_info:
                    self.stdout.write(self.style.WARNING(f"⚠️  Unknown account number: {acct_num}. Skipping line."))
                    continue

                debit = float(row["debit amount"])
                credit = float(row["credit amount"])
                if debit == 0 and credit == 0:
                    continue

                posting_type = "Debit" if debit > 0 else "Credit"
                amount = debit if debit > 0 else credit

                line = {
                    "DetailType": "JournalEntryLineDetail",
                    "Amount": round(amount, 2),
                    "Description": row["reference"],
                    "JournalEntryLineDetail": {
                        "PostingType": posting_type,
                        "AccountRef": {
                            "value": account_info["value"],
                            "name": account_info["name"]
                        }
                    }
                }

                lines.append(line)
                total_debit += debit
                total_credit += credit

            # Validate line count and balance
            if len(lines) < 2:
                self.stdout.write(self.style.ERROR(f"❌ Journal {journal_id} has < 2 valid lines. Skipping."))
                continue

            if round(total_debit, 2) != round(total_credit, 2):
                self.stdout.write(self.style.ERROR(
                    f"❌ Journal {journal_id} is not balanced. Debits: {total_debit}, Credits: {total_credit}. Skipping."
                ))
                continue

            payload = {
                "Line": lines,
                "TxnDate": parse_csv_date(rows[0]["date"])
            }

            self.stdout.write(f"📤 Posting journal {journal_id} with {len(lines)} lines")
            # self.stdout.write(json.dumps(payload, indent=2))

            company_id = get_company_id()
            url = f"https://quickbooks.api.intuit.com/v3/company/{company_id}/journalentry"
            headers = get_qbo_headers()
            response = requests.post(url, headers=headers, json=payload)

            JournalEntry.objects.get_or_create(
                journal_id=journal_id,
                defaults={
                    "date": parse_csv_date(rows[0]["date"]),
                    "reference": rows[0].get("reference", ""),
                    "qbo_response": response.text,
                    "posted_to_qbo": response.status_code == 200,
                    "posted_at": now() if response.status_code == 200 else None,
                }
            )

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f"✅ Posted journal {journal_id} successfully"))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Failed to post journal {journal_id}: {response.status_code} - {response.text}"
                ))
