"""
Create Avalara ReturnInvoice credits for overpayments caused by legacy address logic.
Uses the same CSV as the compare command; finds transactions in Avalara by customer + amount;
creates one credit per match with docCode {originalCode}_CREDIT.
"""

from django.core.management.base import BaseCommand
import pandas as pd
import base64
import requests
import csv
import time
import json
from datetime import datetime
from pathlib import Path

# Sentinel: cache this for an address when GET byaddress fails so we don't retry
RATE_FETCH_FAILED = None

TAXRATES_BYADDRESS_URL = "https://rest.avatax.com/api/v2/taxrates/byaddress"

# Wheat Ridge address for credit transactions (8% nominal rate)
WHEAT_RIDGE_ADDRESS = {
    "line1": "11722 W 44th Ave",
    "city": "Wheat Ridge",
    "region": "CO",
    "country": "US",
    "postalCode": "80033",
}

# Tolerance for matching Avalara totalTax/totalAmount to our computed values.
# Allow a few cents for rounding differences between our rate-based calc and Avalara's stored transaction.
TAX_MATCH_TOLERANCE = 0.10
AMOUNT_MATCH_TOLERANCE = 0.10


def _address_key(ship_to):
    """Unique key for caching rate by ship-to address."""
    return (
        str(ship_to.get("line1", "")),
        str(ship_to.get("city", "")),
        str(ship_to.get("region", "")),
        str(ship_to.get("postalCode", "")),
        str(ship_to.get("country", "US")),
    )


class Command(BaseCommand):
    help = (
        "Find invoices where Avatax (legacy address) tax differs from CSV tax, "
        "match them to Avalara transactions by customer + amount, and create "
        "ReturnInvoice credits for the overpayment (docCode {original}_CREDIT)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to the invoice CSV (same format as compare command; must include SaleType, InvoiceDate, etc.). "
            "Optional column AvalaraDocumentCode: when the list API does not return a transaction (e.g. Locked), add the document code from the Avalara UI to look it up by code.",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            required=True,
            dest="start_date",
            help="Start of date range for querying Avalara (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            required=True,
            dest="end_date",
            help="End of date range for querying Avalara (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--diff",
            type=float,
            default=0,
            dest="diff",
            help="Only process invoices where |tax difference| is greater than this amount (e.g. 100 for $100). Default: 0.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Preview what would be created without calling Avalara create.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.2,
            dest="delay",
            help="Seconds to wait after each Avalara API call. Default: 0.2.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            dest="verbose",
            help="Print how many transactions were returned from Avalara and sample field names for debugging.",
        )

    def _get_rate_for_address(self, ship_to, headers, rate_cache, delay_after_request=0):
        """Return totalRate (float) for ship_to, from cache or GET byaddress. On failure return None."""
        key = _address_key(ship_to)
        if key in rate_cache:
            return rate_cache[key]

        params = {
            "line1": ship_to.get("line1", ""),
            "city": ship_to.get("city", ""),
            "region": ship_to.get("region", ""),
            "postalCode": str(ship_to.get("postalCode", "")).strip(),
            "country": ship_to.get("country", "US"),
        }

        try:
            response = requests.get(TAXRATES_BYADDRESS_URL, params=params, headers=headers, timeout=30)
        except Exception:
            rate_cache[key] = RATE_FETCH_FAILED
            if delay_after_request > 0:
                time.sleep(delay_after_request)
            return None

        if response.status_code >= 400:
            rate_cache[key] = RATE_FETCH_FAILED
            if delay_after_request > 0:
                time.sleep(delay_after_request)
            return None

        try:
            data = response.json()
            rate = data.get("totalRate")
            if rate is None:
                rate_cache[key] = RATE_FETCH_FAILED
                if delay_after_request > 0:
                    time.sleep(delay_after_request)
                return None
            rate_cache[key] = float(rate)
            if delay_after_request > 0:
                time.sleep(delay_after_request)
            return rate_cache[key]
        except (ValueError, TypeError):
            rate_cache[key] = RATE_FETCH_FAILED
            if delay_after_request > 0:
                time.sleep(delay_after_request)
            return None

    def _run_legacy_comparison(self, grouped, headers, rate_cache, options):
        """
        Legacy address logic: delivery if present else branch.
        Returns list of dicts: invoice_id, customer_id, invoice_date, csv_tax, avalara_tax, tax_diff, total_amount.
        Only rows where abs(tax_diff) > diff.
        """
        diff = options["diff"]
        delay = options.get("delay", 0.2)
        rows = []

        for invoice_id, group in grouped:
            first = group.iloc[0]
            total_tax = float(group["TotalTax"].sum())
            branch_id = int(first["BranchID"])

            if branch_id == 2:
                ship_from = {
                    "line1": "11722 W 44th Ave",
                    "city": "Wheat Ridge",
                    "region": "CO",
                    "country": "US",
                    "postalCode": "80033",
                }
            elif branch_id == 3:
                ship_from = {
                    "line1": "10605 Charter Oak Ranch Rd",
                    "city": "Fountain",
                    "region": "CO",
                    "country": "US",
                    "postalCode": "80817",
                }
            else:
                ship_from = {
                    "line1": "5075 Tabor St",
                    "city": "Wheat Ridge",
                    "region": "CO",
                    "country": "US",
                    "postalCode": "80033",
                }

            delivery_raw = first.get("DeliveryAddressLine1", "")
            delivery_str = str(delivery_raw).strip() if delivery_raw is not None else ""
            has_delivery = bool(delivery_str and delivery_str.upper() != "NULL")

            if has_delivery:
                ship_to = {
                    "line1": first["DeliveryAddressLine1"],
                    "city": first["DeliveryCity"],
                    "region": first["DeliveryCounty"],
                    "country": "US",
                    "postalCode": str(first["DeliveryPostCode"]).strip() or ship_from["postalCode"],
                }
            else:
                ship_to = ship_from.copy()

            if total_tax == 0:
                total_amount = sum(
                    float(row["TotalAmount"])
                    for _, row in group.iterrows()
                    if "DC - Delivery Charge" not in str(row["Description"])
                )
                rows.append({
                    "invoice_id": invoice_id,
                    "customer_id": int(first["CustomerID"]),
                    "invoice_date": pd.to_datetime(first["InvoiceDate"]).strftime("%Y-%m-%d"),
                    "csv_tax": 0.0,
                    "avalara_tax": 0.0,
                    "tax_diff": 0.0,
                    "total_amount": total_amount,
                })
                continue

            total_rate = self._get_rate_for_address(ship_to, headers, rate_cache, delay)
            if total_rate is None:
                self.stdout.write(
                    self.style.ERROR(f"[Invoice {invoice_id}] Could not get tax rate for address.")
                )
                continue

            total_amount = 0.0
            for _, row in group.iterrows():
                if "DC - Delivery Charge" not in str(row["Description"]):
                    total_amount += float(row["TotalAmount"])

            avalara_tax = 0.0
            for _, row in group.iterrows():
                description = str(row["Description"])
                amount = float(row["TotalAmount"])
                if "DC - Delivery Charge" in description:
                    line_tax = 0.0
                else:
                    line_tax = round(amount * total_rate, 2)
                avalara_tax += line_tax

            tax_diff = avalara_tax - total_tax
            # Optional: CSV column AvalaraDocumentCode to look up transaction by code (list API may omit Locked txns)
            avalara_doc_code = None
            if "AvalaraDocumentCode" in group.columns:
                raw = first.get("AvalaraDocumentCode", "")
                if pd.notna(raw) and str(raw).strip():
                    avalara_doc_code = str(raw).strip()
            row_dict = {
                "invoice_id": invoice_id,
                "customer_id": int(first["CustomerID"]),
                "invoice_date": pd.to_datetime(first["InvoiceDate"]).strftime("%Y-%m-%d"),
                "csv_tax": total_tax,
                "avalara_tax": round(avalara_tax, 2),
                "tax_diff": round(tax_diff, 2),
                "total_amount": round(total_amount, 2),
            }
            if avalara_doc_code:
                row_dict["avalara_document_code"] = avalara_doc_code
            rows.append(row_dict)

        # Only rows where absolute tax difference exceeds threshold
        filtered = [r for r in rows if abs(r["tax_diff"]) > diff]
        # Only overpayments (positive tax_diff) get credits
        filtered = [r for r in filtered if r["tax_diff"] > 0]
        filtered.sort(key=lambda x: x["tax_diff"], reverse=True)
        return filtered

    def _list_transactions_for_customer(self, company_code, headers, customer_code, start_date, end_date, delay=0, verbose=False):
        """GET Avalara transactions for company in date range. Filter by customerCode via $filter or client-side fallback."""
        url = f"https://rest.avatax.com/api/v2/companies/{company_code}/transactions"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "$filter": f"customerCode eq '{customer_code}'",
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"List transactions request failed: {e}"))
            return []

        if response.status_code >= 400:
            self.stdout.write(
                self.style.ERROR(f"List transactions returned {response.status_code}: {response.text[:200]}")
            )
            return []

        data = response.json()
        transactions = list(data.get("value", []))

        next_link = data.get("@odata.nextLink")
        while next_link:
            if delay > 0:
                time.sleep(delay)
            try:
                next_response = requests.get(next_link, headers=headers, timeout=30)
            except Exception:
                break
            if next_response.status_code != 200:
                break
            next_data = next_response.json()
            transactions.extend(next_data.get("value", []))
            next_link = next_data.get("@odata.nextLink")

        # If filter returned nothing, try without filter and filter client-side (some APIs ignore $filter on this endpoint)
        if not transactions:
            params_no_filter = {"startDate": start_date, "endDate": end_date}
            try:
                response2 = requests.get(url, headers=headers, params=params_no_filter, timeout=30)
            except Exception as e:
                if verbose:
                    self.stdout.write(self.style.WARNING(f"Fallback list (no filter) failed: {e}"))
                return []
            if response2.status_code == 200:
                data2 = response2.json()
                all_txns = list(data2.get("value", []))
                next_link = data2.get("@odata.nextLink")
                while next_link:
                    if delay > 0:
                        time.sleep(delay)
                    try:
                        next_response = requests.get(next_link, headers=headers, timeout=30)
                    except Exception:
                        break
                    if next_response.status_code != 200:
                        break
                    next_data = next_response.json()
                    all_txns.extend(next_data.get("value", []))
                    next_link = next_data.get("@odata.nextLink")
                transactions = [t for t in all_txns if str(t.get("customerCode") or t.get("customer_code") or "") == str(customer_code)]

        if verbose and transactions:
            first = transactions[0]
            self.stdout.write(f"  [Verbose] Found {len(transactions)} transaction(s). First transaction keys: {list(first.keys())}")
            for k in ("code", "id", "documentCode", "totalTax", "totalAmount", "amount", "customerCode"):
                if k in first:
                    self.stdout.write(f"  [Verbose]   {k} = {first[k]}")
        elif verbose and not transactions:
            self.stdout.write("  [Verbose] No transactions returned from Avalara for this customer/date range.")

        return transactions

    def _get_transaction_by_code(self, company_code, headers, document_code):
        """GET a single transaction by document code. Returns the transaction dict or None."""
        url = f"https://rest.avatax.com/api/v2/companies/{company_code}/transactions/{document_code}"
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Get transaction by code failed: {e}"))
            return None
        if response.status_code >= 400:
            if response.status_code == 404:
                return None
            self.stdout.write(
                self.style.ERROR(f"Get transaction by code returned {response.status_code}: {response.text[:200]}")
            )
            return None
        try:
            return response.json()
        except Exception:
            return None

    def _get_txn_tax_and_amount(self, txn):
        """Extract totalTax and totalAmount from a transaction dict; Avalara may use different keys."""
        txn_tax = txn.get("totalTax") or txn.get("tax") or txn.get("totalTaxAmount")
        txn_amount = txn.get("totalAmount") or txn.get("amount")
        try:
            txn_tax = float(txn_tax) if txn_tax is not None else None
            txn_amount = float(txn_amount) if txn_amount is not None else None
        except (TypeError, ValueError):
            return None, None
        return txn_tax, txn_amount

    def _get_txn_doc_code(self, txn):
        """Extract document code from a transaction dict."""
        return txn.get("code") or txn.get("id") or txn.get("documentCode")

    def _find_matching_transaction(self, transactions, avalara_tax, total_amount):
        """
        Find a transaction where totalTax ≈ avalara_tax and totalAmount ≈ total_amount.
        Avalara response may use 'totalTax', 'totalAmount'; or nested/slightly different names.
        Returns the transaction dict or None.
        """
        for txn in transactions:
            txn_tax, txn_amount = self._get_txn_tax_and_amount(txn)
            if txn_tax is None:
                continue
            tax_ok = abs(txn_tax - avalara_tax) <= TAX_MATCH_TOLERANCE
            amount_ok = txn_amount is None or abs(txn_amount - total_amount) <= AMOUNT_MATCH_TOLERANCE
            if tax_ok and amount_ok:
                return txn
        # Fallback: match by tax only
        for txn in transactions:
            txn_tax, _ = self._get_txn_tax_and_amount(txn)
            if txn_tax is not None and abs(txn_tax - avalara_tax) <= TAX_MATCH_TOLERANCE:
                return txn
        return None

    def _create_credit_transaction(self, headers, company_code, original_code, customer_code, tax_diff, document_date):
        """
        Build and POST a ReturnInvoice credit. tax_diff is positive = overpayment;
        we create a credit with tax amount = tax_diff (negative line/override for return).
        document_date: YYYY-MM-DD to match the original transaction (from CSV InvoiceDate).
        """
        credit_tax = round(abs(tax_diff), 2)
        # Line amount so that at 8% nominal we have a base; override sets exact tax
        line_amount = -round(credit_tax / 0.08, 2)
        total_amount = line_amount - credit_tax

        line = {
            "number": "1",
            "quantity": 1,
            "amount": line_amount,
            "taxCode": "P0000000",
            "itemCode": "CREDIT_0001",
            "description": "Overpayment adjustment",
            "taxOverride": {
                "type": "TaxAmount",
                "taxAmount": -credit_tax,
                "reason": "Adding credit for overpayment",
            },
        }

        # Use original transaction date so document date and tax date match the invoice
        transaction_data = {
            "type": "ReturnInvoice",
            "companyCode": str(company_code),
            "date": document_date,
            "taxDate": document_date,
            "customerCode": str(customer_code),
            "docCode": f"{original_code}_CREDIT",
            "exemptionNo": "",
            "totalAmount": total_amount,
            "totalTax": -credit_tax,
            "currencyCode": "USD",
            "commit": True,
            "addresses": {
                "shipFrom": WHEAT_RIDGE_ADDRESS,
                "shipTo": WHEAT_RIDGE_ADDRESS,
            },
            "lines": [line],
        }

        response = requests.post(
            "https://rest.avatax.com/api/v2/transactions/create",
            headers=headers,
            data=json.dumps(transaction_data),
            timeout=30,
        )
        return response

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        start_date = options["start_date"]
        end_date = options["end_date"]
        diff = options["diff"]
        dry_run = options.get("dry_run", False)
        delay = options.get("delay", 0.2)

        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()

        required = ["SaleType", "InvoiceID", "CustomerID", "BranchID", "TotalTax", "TotalAmount", "Description", "InvoiceDate"]
        for col in required:
            if col not in df.columns:
                self.stdout.write(self.style.ERROR(f"CSV must contain column: {col}"))
                return

        df["InvoiceID"] = df["InvoiceID"].astype(int)
        df["CustomerID"] = df["CustomerID"].astype(int)
        df["SaleType"] = df["SaleType"].astype(int)
        for col in ["DeliveryAddressLine1", "DeliveryCity", "DeliveryCounty", "DeliveryPostCode"]:
            if col in df.columns:
                df[col] = df[col].fillna("")

        account_number = 2000899182
        license_key = "CFF176791390F51C"
        company_code = 157753

        auth_string = f"{account_number}:{license_key}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/json",
            "X-Avalara-Client": "DjangoTaxApp; 1.0; Production; Self",
        }

        grouped = df.groupby("InvoiceID")
        rate_cache = {}

        self.stdout.write("Running legacy address comparison...")
        discrepancy_rows = self._run_legacy_comparison(grouped, headers, rate_cache, options)

        if not discrepancy_rows:
            self.stdout.write(self.style.SUCCESS(
                f"No overpayment invoices with tax diff > {diff}. Nothing to do."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Found {len(discrepancy_rows)} overpayment invoice(s) with tax diff > {diff}."
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: no transactions will be created."))

        created = 0
        no_match = 0
        error_log = []
        error_log_path = Path("avalara_legacy_credit_errors.csv")

        for row in discrepancy_rows:
            invoice_id = row["invoice_id"]
            customer_id = row["customer_id"]
            customer_code = str(customer_id)
            avalara_tax = row["avalara_tax"]
            tax_diff = row["tax_diff"]
            total_amount = row["total_amount"]

            if delay > 0:
                time.sleep(delay)

            match = None
            # Optional: use Avalara document code from CSV (list API often omits Locked/Committed txns)
            doc_code_from_csv = row.get("avalara_document_code")
            if doc_code_from_csv:
                txn = self._get_transaction_by_code(company_code, headers, doc_code_from_csv)
                if txn and str(txn.get("customerCode") or "") == customer_code:
                    txn_tax, txn_amount = self._get_txn_tax_and_amount(txn)
                    if txn_tax is not None and abs(txn_tax - avalara_tax) <= TAX_MATCH_TOLERANCE:
                        if txn_amount is None or abs(txn_amount - total_amount) <= AMOUNT_MATCH_TOLERANCE:
                            match = txn
                if not match and txn:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[Invoice {invoice_id}] Transaction {doc_code_from_csv} found but customer/amount/tax mismatch. Trying list..."
                        )
                    )

            if not match:
                transactions = self._list_transactions_for_customer(
                    company_code, headers, customer_code, start_date, end_date, delay=delay, verbose=options.get("verbose", False)
                )
                match = self._find_matching_transaction(transactions, avalara_tax, total_amount)

            if not match:
                self.stdout.write(
                    self.style.WARNING(
                        f"[Invoice {invoice_id}] No Avalara transaction found for customer {customer_code} "
                        f"(avalara_tax={avalara_tax}, total_amount={total_amount}). "
                        "Add optional CSV column AvalaraDocumentCode with the transaction code from Avalara UI to match Locked txns."
                    )
                )
                no_match += 1
                continue

            # Document code: AvaTax may return 'code', 'id', or 'documentCode'
            original_code = self._get_txn_doc_code(match)
            if not original_code:
                self.stdout.write(
                    self.style.ERROR(f"[Invoice {invoice_id}] Matched transaction has no code/id. Skipping.")
                )
                no_match += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would create credit: original docCode={original_code}, "
                    f"new docCode={original_code}_CREDIT, customer={customer_code}, "
                    f"tax_diff=${tax_diff:,.2f}, credit_tax=${abs(tax_diff):,.2f}"
                )
                created += 1
                continue

            response = self._create_credit_transaction(
                headers, company_code, original_code, customer_code, tax_diff,
                document_date=row["invoice_date"],
            )

            if response.status_code >= 400:
                try:
                    err = response.json()
                    message = err.get("error", {}).get("message", response.text[:200])
                except Exception:
                    message = response.text[:200]
                self.stdout.write(self.style.ERROR(
                    f"[Invoice {invoice_id}] Credit create failed: {message}"
                ))
                error_log.append({
                    "InvoiceID": invoice_id,
                    "CustomerID": customer_id,
                    "OriginalDocCode": original_code,
                    "StatusCode": response.status_code,
                    "ErrorMessage": message,
                    "FullResponse": response.text[:500],
                })
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"[Invoice {invoice_id}] Credit created: {original_code}_CREDIT"
                ))
                created += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("--- Summary ---"))
        self.stdout.write(f"Credits created: {created}")
        self.stdout.write(f"No match in Avalara: {no_match}")
        self.stdout.write(f"Errors: {len(error_log)}")

        if error_log:
            with open(error_log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=error_log[0].keys())
                writer.writeheader()
                writer.writerows(error_log)
            self.stdout.write(self.style.WARNING(f"Errors written to {error_log_path.resolve()}"))
