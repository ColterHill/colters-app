from django.core.management.base import BaseCommand
import pandas as pd
import base64
import requests
import csv
import time
from pathlib import Path

# SaleType: 2 = will-call (use branch address), 3 = delivery (use customer address)
SALE_TYPE_WILL_CALL = 2
SALE_TYPE_DELIVERY = 3

# Sentinel: cache this for an address when GET byaddress fails so we don't retry
RATE_FETCH_FAILED = None

TAXRATES_BYADDRESS_URL = "https://rest.avatax.com/api/v2/taxrates/byaddress"


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
        "Compare CSV invoice TotalTax vs Avalara rate-based estimated tax. "
        "Uses GET taxrates/byaddress only (no transactions). SaleType: 2=will-call, 3=delivery."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file (must include SaleType column)")
        parser.add_argument(
            "--delay",
            type=float,
            default=0.2,
            help="Seconds to wait after each Avalara API call (only when a new address is requested). Use 0 for no delay. Default: 0.2.",
        )
        parser.add_argument(
            "--top-discrepancies",
            type=int,
            default=0,
            dest="top_discrepancies",
            help="Show top N invoices by absolute tax discrepancy (CSV TotalTax vs Avalara estimate). 0 = do not show. Default: 0.",
        )
        parser.add_argument(
            "--audit-willcall-with-address",
            action="store_true",
            dest="audit_willcall_with_address",
            help="Audit only will-call orders that have a delivery address; compare CSV vs Avalara at delivery address and list by tax difference (for overpayment analysis).",
        )
        parser.add_argument(
            "--legacy-address-min-diff",
            type=float,
            default=0,
            dest="legacy_address_min_diff",
            help="Use legacy address logic (delivery if present else branch) for all invoices; show only rows where |tax difference| is greater than this amount (e.g. 100 for $100). Same table as audit. Default: 0 (off).",
        )
        parser.add_argument(
            "--legacy-address-csv",
            nargs="?",
            const="legacy_address_comparison.csv",
            default=None,
            dest="legacy_address_csv",
            metavar="PATH",
            help="When using --legacy-address-min-diff, also write results to a CSV. If PATH is given, use that file; if omitted (e.g. just --legacy-address-csv), write to legacy_address_comparison.csv.",
        )

    def _get_rate_for_address(self, ship_to, headers, rate_cache, delay_after_request=0):
        """Return totalRate (float) for ship_to, from cache or GET byaddress. On failure return None and cache failure."""
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
        except Exception as e:
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
            # totalRate is a decimal e.g. 0.0825 for 8.25%
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

    def _run_audit_willcall_with_address(self, grouped, headers, rate_cache, options):
        """Audit only will-call (SaleType=2) invoices that have a delivery address; use delivery address for Avalara, compare and list by tax difference descending."""
        audit_rows = []
        delay = options.get("delay", 0.2)

        for invoice_id, group in grouped:
            first = group.iloc[0]
            sale_type = int(first["SaleType"])
            delivery_raw = first.get("DeliveryAddressLine1", "")
            delivery_str = str(delivery_raw).strip() if delivery_raw is not None else ""
            has_delivery = bool(delivery_str and delivery_str.upper() != "NULL")

            if not (sale_type == SALE_TYPE_WILL_CALL and has_delivery):
                continue

            total_tax = group["TotalTax"].sum()
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

            ship_to = {
                "line1": first["DeliveryAddressLine1"],
                "city": first["DeliveryCity"],
                "region": first["DeliveryCounty"],
                "country": "US",
                "postalCode": str(first["DeliveryPostCode"]).strip() or ship_from["postalCode"],
            }

            total_rate = self._get_rate_for_address(ship_to, headers, rate_cache, delay)
            if total_rate is None:
                addr = f"{ship_to.get('line1', '')}, {ship_to.get('city', '')}, {ship_to.get('region', '')} {ship_to.get('postalCode', '')}, {ship_to.get('country', 'US')}"
                self.stdout.write(
                    self.style.ERROR(f"[Invoice {invoice_id}] Could not get tax rate for address: {addr}")
                )
                continue

            taxable_amount = 0.0
            for _, row in group.iterrows():
                if "DC - Delivery Charge" not in str(row["Description"]):
                    taxable_amount += float(row["TotalAmount"])
            csv_rate = total_tax / taxable_amount if taxable_amount > 0 else 0.0

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
            rate_diff_pct = (total_rate - csv_rate) * 100
            audit_rows.append((
                invoice_id,
                total_tax,
                avalara_tax,
                tax_diff,
                csv_rate * 100,
                total_rate * 100,
                rate_diff_pct,
            ))

        audit_rows.sort(key=lambda x: x[3], reverse=True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("--- Will-call with delivery address: CSV vs Avalara at delivery address ---"))
        self.stdout.write(
            f"{'InvoiceID':<12} {'CSV TotalTax':>14} {'Avalara Tax':>14} {'Tax Diff':>12} "
            f"{'CSV Rate %':>10} {'Avalara Rate %':>14} {'Rate Diff (pct pt)':>18}"
        )
        for inv_id, csv_tax, aval_tax, tax_diff, csv_pct, aval_pct, rate_diff in audit_rows:
            self.stdout.write(
                f"{inv_id:<12} ${csv_tax:>12,.2f} ${aval_tax:>12,.2f} ${tax_diff:>10,.2f} "
                f"{csv_pct:>9.2f}% {aval_pct:>13.2f}% {rate_diff:>17.2f}"
            )

        self.stdout.write("")
        self.stdout.write(f"Invoices audited: {len(audit_rows)}")
        sum_diff = sum(r[3] for r in audit_rows)
        self.stdout.write(f"Sum of tax difference (Avalara - CSV): ${sum_diff:,.2f}")
        sum_overpayments = sum(r[3] for r in audit_rows if r[3] > 0)
        self.stdout.write(f"Sum of overpayments (positive diffs only): ${sum_overpayments:,.2f}")

    def _run_legacy_address_comparison(self, grouped, headers, rate_cache, options):
        """Use legacy address logic (delivery if present else branch) for all invoices; show only rows where |tax diff| > min_diff. Same table as audit."""
        min_diff = options["legacy_address_min_diff"]
        delay = options.get("delay", 0.2)
        legacy_rows = []

        for invoice_id, group in grouped:
            first = group.iloc[0]
            total_tax = group["TotalTax"].sum()
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

            # Legacy: delivery address if present (and not "NULL"), else branch
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

            # Exempt: CSV $0 -> Avalara $0
            if total_tax == 0:
                taxable_amount = 0.0
                for _, row in group.iterrows():
                    if "DC - Delivery Charge" not in str(row["Description"]):
                        taxable_amount += float(row["TotalAmount"])
                csv_rate = 0.0
                legacy_rows.append((invoice_id, total_tax, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
                continue

            total_rate = self._get_rate_for_address(ship_to, headers, rate_cache, delay)
            if total_rate is None:
                addr = f"{ship_to.get('line1', '')}, {ship_to.get('city', '')}, {ship_to.get('region', '')} {ship_to.get('postalCode', '')}, {ship_to.get('country', 'US')}"
                self.stdout.write(
                    self.style.ERROR(f"[Invoice {invoice_id}] Could not get tax rate for address: {addr}")
                )
                continue

            taxable_amount = 0.0
            for _, row in group.iterrows():
                if "DC - Delivery Charge" not in str(row["Description"]):
                    taxable_amount += float(row["TotalAmount"])
            csv_rate = total_tax / taxable_amount if taxable_amount > 0 else 0.0

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
            rate_diff_pct = (total_rate - csv_rate) * 100
            amount_at_8pct = round(tax_diff / 0.08, 2)
            legacy_rows.append((
                invoice_id,
                total_tax,
                avalara_tax,
                tax_diff,
                csv_rate * 100,
                total_rate * 100,
                rate_diff_pct,
                amount_at_8pct,
            ))

        filtered = [r for r in legacy_rows if abs(r[3]) > min_diff]
        filtered.sort(key=lambda x: x[3], reverse=True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"--- Legacy address (delivery if present): invoices with |tax diff| > ${min_diff:,.0f} ---"
        ))
        self.stdout.write(
            f"{'InvoiceID':<12} {'CSV TotalTax':>14} {'Avalara Tax':>14} {'Tax Diff':>12} "
            f"{'CSV Rate %':>10} {'Avalara Rate %':>14} {'Rate Diff (pct pt)':>18} {'Amt @ 8%':>12}"
        )
        for inv_id, csv_tax, aval_tax, tax_diff, csv_pct, aval_pct, rate_diff, amt_8 in filtered:
            self.stdout.write(
                f"{inv_id:<12} ${csv_tax:>12,.2f} ${aval_tax:>12,.2f} ${tax_diff:>10,.2f} "
                f"{csv_pct:>9.2f}% {aval_pct:>13.2f}% {rate_diff:>17.2f} ${amt_8:>10,.2f}"
            )

        self.stdout.write("")
        self.stdout.write(f"Invoices shown (|diff| > ${min_diff:,.0f}): {len(filtered)}")
        sum_diff = sum(r[3] for r in filtered)
        self.stdout.write(f"Sum of tax difference (Avalara - CSV): ${sum_diff:,.2f}")
        sum_overpayments = sum(r[3] for r in filtered if r[3] > 0)
        self.stdout.write(f"Sum of overpayments (positive diffs only): ${sum_overpayments:,.2f}")

        csv_path = options.get("legacy_address_csv") or ""
        if csv_path:
            out_path = Path(csv_path.strip())
            with open(out_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "InvoiceID", "CSV_TotalTax", "Avalara_Tax", "Tax_Diff",
                    "CSV_Rate_Pct", "Avalara_Rate_Pct", "Rate_Diff_Pct_Pt", "Amount_At_8pct",
                ])
                for inv_id, csv_tax, aval_tax, tax_diff, csv_pct, aval_pct, rate_diff, amt_8 in filtered:
                    # Round currency to 2 decimals, percentages to 2 decimals for clean CSV output
                    writer.writerow([
                        inv_id,
                        round(csv_tax, 2),
                        round(aval_tax, 2),
                        round(tax_diff, 2),
                        round(csv_pct, 2),
                        round(aval_pct, 2),
                        round(rate_diff, 2),
                        round(amt_8, 2),
                    ])
            self.stdout.write(f"Results written to {out_path.resolve()}")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        df = pd.read_csv(csv_path)

        # Clean headers (in case of leading/trailing spaces)
        df.columns = df.columns.str.strip()

        if "SaleType" not in df.columns:
            self.stdout.write(
                self.style.ERROR("CSV must contain a SaleType column (2=will-call, 3=delivery).")
            )
            return

        # Convert InvoiceID and CustomerID to integers to avoid float representation (.0)
        df["InvoiceID"] = df["InvoiceID"].astype(int)
        df["CustomerID"] = df["CustomerID"].astype(int)
        df["SaleType"] = df["SaleType"].astype(int)

        # Clean up possible NaN values in delivery fields
        for col in ["DeliveryAddressLine1", "DeliveryCity", "DeliveryCounty", "DeliveryPostCode"]:
            df[col] = df[col].fillna("")

        # Setup Avalara credentials (same as existing commands)
        account_number = 2000899182
        license_key = "CFF176791390F51C"

        auth_string = f"{account_number}:{license_key}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "X-Avalara-Client": "DjangoTaxApp; 1.0; Production; Self",
        }

        grouped = df.groupby("InvoiceID")
        rate_cache = {}  # address_key -> totalRate (float) or RATE_FETCH_FAILED (None)

        # Legacy address mode: delivery if present else branch; show only |tax diff| > min_diff
        if options.get("legacy_address_min_diff", 0) > 0:
            self._run_legacy_address_comparison(grouped, headers, rate_cache, options)
            return

        # Audit mode: only will-call + delivery address; CSV vs Avalara at delivery address, sorted by tax diff desc
        if options.get("audit_willcall_with_address"):
            self._run_audit_willcall_with_address(grouped, headers, rate_cache, options)
            return

        csv_total_tax = 0.0
        avalara_total_tax = 0.0
        processed_count = 0
        error_log = []
        error_log_path = Path("avalara_compare_tax_errors.csv")

        top_n = options.get("top_discrepancies", 0)
        discrepancy_list = [] if top_n > 0 else None

        for invoice_id, group in grouped:
            first = group.iloc[0]
            branch_id = int(first["BranchID"])
            sale_type = int(first["SaleType"])

            total_tax = group["TotalTax"].sum()
            csv_total_tax += total_tax

            # Tax-exempt orders: CSV $0 means Avalara $0 (no rate lookup)
            if total_tax == 0:
                invoice_estimated_tax = 0.0
                avalara_total_tax += invoice_estimated_tax
                processed_count += 1
                if discrepancy_list is not None:
                    discrepancy_list.append((invoice_id, total_tax, invoice_estimated_tax, 0.0))
                continue

            # Determine ship-from address based on BranchID
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

            # Ship-to: SaleType 2 = will-call (branch address), 3 = delivery (customer address or fallback to branch)
            if sale_type == SALE_TYPE_WILL_CALL:
                ship_to = ship_from.copy()
            elif sale_type == SALE_TYPE_DELIVERY:
                if first["DeliveryAddressLine1"]:
                    ship_to = {
                        "line1": first["DeliveryAddressLine1"],
                        "city": first["DeliveryCity"],
                        "region": first["DeliveryCounty"],
                        "country": "US",
                        "postalCode": str(first["DeliveryPostCode"]).strip() or ship_from["postalCode"],
                    }
                else:
                    ship_to = ship_from.copy()
            else:
                if first["DeliveryAddressLine1"]:
                    ship_to = {
                        "line1": first["DeliveryAddressLine1"],
                        "city": first["DeliveryCity"],
                        "region": first["DeliveryCounty"],
                        "country": "US",
                        "postalCode": str(first["DeliveryPostCode"]).strip() or ship_from["postalCode"],
                    }
                else:
                    ship_to = ship_from.copy()

            total_rate = self._get_rate_for_address(ship_to, headers, rate_cache, options["delay"])
            if total_rate is None:
                self.stdout.write(
                    self.style.ERROR(f"[Invoice {invoice_id}] Could not get tax rate for address.")
                )
                error_log.append({
                    "InvoiceID": invoice_id,
                    "Address": str(ship_to),
                    "ErrorMessage": "GET taxrates/byaddress failed or missing totalRate",
                })
                continue

            # Estimated tax: for each line, if DC - Delivery Charge then 0 else amount * totalRate; round to 2 decimals per line
            invoice_estimated_tax = 0.0
            for _, row in group.iterrows():
                description = str(row["Description"])
                amount = float(row["TotalAmount"])
                if "DC - Delivery Charge" in description:
                    line_tax = 0.0
                else:
                    line_tax = round(amount * total_rate, 2)
                invoice_estimated_tax += line_tax

            avalara_total_tax += invoice_estimated_tax
            processed_count += 1

            if discrepancy_list is not None:
                difference = invoice_estimated_tax - total_tax
                discrepancy_list.append((invoice_id, total_tax, invoice_estimated_tax, difference))

        # Top discrepancies (before summary)
        if top_n > 0 and discrepancy_list:
            sorted_list = sorted(discrepancy_list, key=lambda x: abs(x[3]), reverse=True)
            top_list = sorted_list[:top_n]
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(f"--- Top {len(top_list)} invoices by tax discrepancy (CSV vs Avalara) ---"))
            self.stdout.write(f"{'InvoiceID':<12} {'CSV TotalTax':>14} {'Avalara Tax':>14} {'Difference':>12}")
            for inv_id, csv_tax, aval_tax, diff in top_list:
                self.stdout.write(f"{inv_id:<12} ${csv_tax:>12,.2f} ${aval_tax:>12,.2f} ${diff:>10,.2f}")

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("--- Summary ---"))
        self.stdout.write(f"CSV total tax:        ${csv_total_tax:,.2f}")
        self.stdout.write(f"Avalara total tax:   ${avalara_total_tax:,.2f}")
        diff = avalara_total_tax - csv_total_tax
        self.stdout.write(f"Difference:           ${diff:,.2f}")
        self.stdout.write(f"Invoices processed:  {processed_count}")
        self.stdout.write(f"Invoices failed:      {len(error_log)}")

        if error_log:
            with open(error_log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=error_log[0].keys())
                writer.writeheader()
                writer.writerows(error_log)
            self.stdout.write(
                self.style.WARNING(f"Errors written to {error_log_path.resolve()}")
            )
