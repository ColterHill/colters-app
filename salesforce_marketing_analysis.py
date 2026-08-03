import os
import sys
import math
import json
import time
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Use a non-interactive backend for headless environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from simple_salesforce import Salesforce
from dotenv import load_dotenv


DEFAULT_CUSTOMER_NAMES: List[str] = [
    "Ned Avery",
    "Stevie Tuck / Andrew Scofield",
    "Nate Barrett",
    "John Clemmons",
    "Wes Gough",
    "Marcus Dickey",
    "Vladan Panic",
    "Andrew Bracken",
    "Jason Oleary",
    "Tim Perri",
    "Mark DeVos",
    "Ulises Tajonar-Diaz",
    "O’banyon Custer",
    "Cory Gill",
    "Ron L Hurtado",
    "Jesus Montelongo",
    "Brad Sanders",
    "Joe Thede",
    "Jason Ingalsbe",
    "Graciano Jimenez",
    "Jesus Dominguez",
]


@dataclass
class SalesforceConfig:
    username: str
    password: str
    security_token: str
    domain: str = "login"  # or "test" for sandbox


def normalize_salesforce_domain(value: str) -> str:
    v = (value or "").strip().lower()
    if not v:
        return "login"
    # strip protocol
    if v.startswith("http://"):
        v = v[len("http://"):]
    elif v.startswith("https://"):
        v = v[len("https://"):]
    # strip trailing slash
    if v.endswith("/"):
        v = v[:-1]
    # collapse known host suffixes to subdomain
    for suffix in [".my.salesforce.com", ".salesforce.com"]:
        if v.endswith(suffix):
            v = v[: -len(suffix)]
            break
    # allowed values: 'login', 'test', or custom my domain subdomain + '.my' (e.g., 'rmfp.my')
    if v in ("login", "test"):
        return v
    # if user provided just the my-domain subdomain, add '.my'
    if v and not v.endswith(".my"):
        v = f"{v}.my"
    return v or "login"


def load_salesforce_config_from_env() -> SalesforceConfig:
    load_dotenv()
    username = os.getenv("SF_USERNAME", "").strip()
    password = os.getenv("SF_PASSWORD", "").strip()
    token = os.getenv("SF_SECURITY_TOKEN", "").strip()
    domain_raw = os.getenv("SF_DOMAIN", "login").strip() or "login"
    domain = normalize_salesforce_domain(domain_raw)

    missing: List[str] = []
    if not username:
        missing.append("SF_USERNAME")
    if not password:
        missing.append("SF_PASSWORD")
    if not token:
        missing.append("SF_SECURITY_TOKEN")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}.\n"
            "Set them in your environment or a .env file."
        )

    return SalesforceConfig(username=username, password=password, security_token=token, domain=domain)


def connect_to_salesforce(config: SalesforceConfig) -> Salesforce:
    return Salesforce(
        username=config.username,
        password=config.password,
        security_token=config.security_token,
        domain=config.domain,
        client_id="ColtersAppMarketingAnalysis/1.0",
    )


def chunk_list(values: List[str], chunk_size: int) -> List[List[str]]:
    return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]


def fetch_accounts_by_names(sf: Salesforce, account_names: List[str]) -> pd.DataFrame:
    if not account_names:
        return pd.DataFrame(columns=["Id", "Name"])

    all_rows: List[Dict[str, str]] = []
    # SOQL IN list limits: keep chunks small to be safe
    for name_chunk in chunk_list(account_names, 50):
        # Escape single quotes in names for SOQL
        escaped_names = [name.replace("'", "\\'") for name in name_chunk]
        in_clause = ",".join([f"'{n}'" for n in escaped_names])
        soql = f"""
            SELECT Id, Name
            FROM Account
            WHERE Name IN ({in_clause})
        """
        for rec in query_all_records(sf, soql):
            all_rows.append({"Id": rec.get("Id"), "Name": rec.get("Name")})

    df = pd.DataFrame(all_rows)
    return df.drop_duplicates(subset=["Id"]) if not df.empty else df


def fetch_closed_won_opportunities(sf: Salesforce, account_ids: List[str]) -> pd.DataFrame:
    if not account_ids:
        return pd.DataFrame(columns=["Id", "AccountId", "Amount", "CloseDate", "StageName"])

    all_rows: List[Dict[str, Optional[str]]] = []

    for id_chunk in chunk_list(account_ids, 200):
        in_clause = ",".join([f"'{i}'" for i in id_chunk])
        soql = f"""
            SELECT Id, AccountId, Amount, CloseDate, StageName
            FROM Opportunity
            WHERE IsWon = true AND AccountId IN ({in_clause})
        """
        for rec in query_all_records(sf, soql):
            all_rows.append(
                {
                    "Id": rec.get("Id"),
                    "AccountId": rec.get("AccountId"),
                    "Amount": rec.get("Amount"),
                    "CloseDate": rec.get("CloseDate"),
                    "StageName": rec.get("StageName"),
                }
            )

    df = pd.DataFrame(all_rows)
    if not df.empty:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
        df["CloseDate"] = pd.to_datetime(df["CloseDate"], errors="coerce")
        df = df.dropna(subset=["CloseDate"])  # require valid dates
        df["Year"] = df["CloseDate"].dt.year.astype(int)
        df["Month"] = df["CloseDate"].dt.month.astype(int)
    return df


def fetch_quote_line_items_for_accounts(sf: Salesforce, account_ids: List[str]) -> pd.DataFrame:
    if not account_ids:
        return pd.DataFrame(
            columns=[
                "Id",
                "Quantity",
                "UnitPrice",
                "ProductFamily",
                "OpportunityAccountId",
                "OpportunityCloseDate",
                "OpportunityIsWon",
            ]
        )

    all_rows: List[Dict[str, Optional[str]]] = []

    for id_chunk in chunk_list(account_ids, 100):
        in_clause = ",".join([f"'{i}'" for i in id_chunk])
        soql = f"""
            SELECT Id,
                   Quantity,
                   UnitPrice,
                   PricebookEntry.Product2.Family,
                   Quote.Opportunity.AccountId,
                   Quote.Opportunity.CloseDate,
                   Quote.Opportunity.IsWon
            FROM QuoteLineItem
            WHERE Quote.Opportunity.AccountId IN ({in_clause})
        """
        for rec in query_all_records(sf, soql):
            product_family = None
            try:
                product_family = (
                    rec.get("PricebookEntry", {})
                    .get("Product2", {})
                    .get("Family")
                )
            except Exception:
                product_family = None

            opp = rec.get("Quote", {}).get("Opportunity", {})

            all_rows.append(
                {
                    "Id": rec.get("Id"),
                    "Quantity": rec.get("Quantity"),
                    "UnitPrice": rec.get("UnitPrice"),
                    "ProductFamily": product_family,
                    "OpportunityAccountId": opp.get("AccountId"),
                    "OpportunityCloseDate": opp.get("CloseDate"),
                    "OpportunityIsWon": opp.get("IsWon"),
                }
            )

    df = pd.DataFrame(all_rows)
    if not df.empty:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0.0)
        df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0.0)
        df["LineAmount"] = df["Quantity"] * df["UnitPrice"]
        df["OpportunityCloseDate"] = pd.to_datetime(df["OpportunityCloseDate"], errors="coerce")
        df = df.dropna(subset=["OpportunityCloseDate"])  # require valid dates
        df["Year"] = df["OpportunityCloseDate"].dt.year.astype(int)
        df["Month"] = df["OpportunityCloseDate"].dt.month.astype(int)
        # Only keep won Opp line items for category/volume analysis
        df = df[df["OpportunityIsWon"] == True]
    return df


def compute_yearly_metrics(opps_df: pd.DataFrame, accounts_df: pd.DataFrame) -> pd.DataFrame:
    if opps_df.empty or accounts_df.empty:
        return pd.DataFrame(columns=[
            "AccountId", "AccountName", "Year", "TotalAmount", "OrderCount", "AveragePerOrder"
        ])

    account_id_to_name: Dict[str, str] = dict(zip(accounts_df["Id"], accounts_df["Name"]))
    grouped = opps_df.groupby(["AccountId", "Year"], as_index=False).agg(
        TotalAmount=("Amount", "sum"),
        OrderCount=("Id", "count"),
    )
    grouped["AveragePerOrder"] = grouped.apply(
        lambda r: (r["TotalAmount"] / r["OrderCount"]) if r["OrderCount"] else 0.0,
        axis=1,
    )
    grouped["AccountName"] = grouped["AccountId"].map(account_id_to_name)
    cols = ["AccountId", "AccountName", "Year", "TotalAmount", "OrderCount", "AveragePerOrder"]
    return grouped[cols].sort_values(["AccountName", "Year"]).reset_index(drop=True)


def compute_monthly_metrics(opps_df: pd.DataFrame, accounts_df: pd.DataFrame) -> pd.DataFrame:
    if opps_df.empty or accounts_df.empty:
        return pd.DataFrame(columns=[
            "AccountId", "AccountName", "Year", "Month", "TotalAmount", "OrderCount"
        ])
    account_id_to_name: Dict[str, str] = dict(zip(accounts_df["Id"], accounts_df["Name"]))
    grouped = opps_df.groupby(["AccountId", "Year", "Month"], as_index=False).agg(
        TotalAmount=("Amount", "sum"),
        OrderCount=("Id", "count"),
    )
    grouped["AccountName"] = grouped["AccountId"].map(account_id_to_name)
    cols = ["AccountId", "AccountName", "Year", "Month", "TotalAmount", "OrderCount"]
    return grouped[cols].sort_values(["AccountName", "Year", "Month"]).reset_index(drop=True)


def compute_top_categories(qli_df: pd.DataFrame, accounts_df: pd.DataFrame) -> pd.DataFrame:
    if qli_df.empty or accounts_df.empty:
        return pd.DataFrame(columns=[
            "AccountId", "AccountName", "Year", "ProductFamily", "LineAmount", "LineCount"
        ])
    account_id_to_name: Dict[str, str] = dict(zip(accounts_df["Id"], accounts_df["Name"]))
    # ProductFamily can be null; bucket nulls
    qli_df = qli_df.copy()
    qli_df["ProductFamily"] = qli_df["ProductFamily"].fillna("Unspecified")
    grouped = qli_df.groupby(["OpportunityAccountId", "Year", "ProductFamily"], as_index=False).agg(
        LineAmount=("LineAmount", "sum"),
        LineCount=("Id", "count"),
    )
    grouped.rename(columns={"OpportunityAccountId": "AccountId"}, inplace=True)
    grouped["AccountName"] = grouped["AccountId"].map(account_id_to_name)
    cols = ["AccountId", "AccountName", "Year", "ProductFamily", "LineAmount", "LineCount"]
    return grouped[cols].sort_values(["AccountName", "Year", "LineAmount"], ascending=[True, True, False]).reset_index(drop=True)


def ensure_output_dirs(base_dir: str) -> Tuple[str, str]:
    csv_dir = os.path.join(base_dir, "output")
    graphs_dir = os.path.join(csv_dir, "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    return csv_dir, graphs_dir


def write_csvs(
    output_dir: str,
    yearly_df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    categories_df: pd.DataFrame,
) -> None:
    yearly_path = os.path.join(output_dir, "customer_yearly_summary.csv")
    monthly_path = os.path.join(output_dir, "customer_monthly_activity.csv")
    categories_path = os.path.join(output_dir, "customer_top_categories.csv")

    yearly_df.to_csv(yearly_path, index=False)
    monthly_df.to_csv(monthly_path, index=False)
    categories_df.to_csv(categories_path, index=False)


def write_excel(
    output_dir: str,
    yearly_df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    categories_df: pd.DataFrame,
) -> None:
    excel_path = os.path.join(output_dir, "marketing_summary.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        yearly_df.to_excel(writer, index=False, sheet_name="Yearly Summary")
        monthly_df.to_excel(writer, index=False, sheet_name="Monthly Activity")
        categories_df.to_excel(writer, index=False, sheet_name="Top Categories")
    
    # Also save a quick pivot per-customer per-year amount for fast scanning
    try:
        pivot = yearly_df.pivot_table(index="AccountName", columns="Year", values="TotalAmount", aggfunc="sum").fillna(0.0)
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            pivot.to_excel(writer, sheet_name="Pivot Amounts")
    except Exception:
        # Non-fatal if pivot fails (e.g., no data)
        pass


def query_all_records(sf: Salesforce, soql: str) -> List[Dict[str, object]]:
    result = sf.query(soql)
    records: List[Dict[str, object]] = list(result.get("records", []))
    while not result.get("done", True):
        next_url = result.get("nextRecordsUrl")
        if not next_url:
            break
        result = sf.query_more(next_url, identifier_is_url=True)
        records.extend(result.get("records", []))
    return records


def sanitize_filename(value: str) -> str:
    invalid_chars = '\\/:*?"<>|'
    for ch in invalid_chars:
        value = value.replace(ch, "_")
    return value


def plot_per_customer_graphs(
    graphs_dir: str,
    account_name: str,
    yearly_df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    categories_df: pd.DataFrame,
) -> None:
    safe_name = sanitize_filename(account_name)

    # Yearly totals and average per order
    ydf = yearly_df[yearly_df["AccountName"] == account_name]
    if not ydf.empty:
        fig, ax1 = plt.subplots(figsize=(9, 5))
        sns.barplot(x="Year", y="TotalAmount", data=ydf, ax=ax1, color="#4C78A8")
        ax1.set_title(f"{account_name} – Yearly Total Amount")
        ax1.set_ylabel("Total Amount")
        ax1.set_xlabel("Year")
        plt.tight_layout()
        fig.savefig(os.path.join(graphs_dir, f"{safe_name}_yearly_total_amount.png"), dpi=150)
        plt.close(fig)

        fig, ax2 = plt.subplots(figsize=(9, 5))
        sns.lineplot(x="Year", y="AveragePerOrder", data=ydf, marker="o", ax=ax2, color="#F58518")
        ax2.set_title(f"{account_name} – Yearly Average Per Order")
        ax2.set_ylabel("Avg Per Order")
        ax2.set_xlabel("Year")
        plt.tight_layout()
        fig.savefig(os.path.join(graphs_dir, f"{safe_name}_yearly_avg_per_order.png"), dpi=150)
        plt.close(fig)

    # Monthly heatmaps (TotalAmount and OrderCount)
    mdf = monthly_df[monthly_df["AccountName"] == account_name]
    if not mdf.empty:
        # Pivot for heatmap
        amt_pivot = mdf.pivot_table(index="Year", columns="Month", values="TotalAmount", aggfunc="sum").fillna(0.0)
        cnt_pivot = mdf.pivot_table(index="Year", columns="Month", values="OrderCount", aggfunc="sum").fillna(0.0)

        fig, ax = plt.subplots(figsize=(11, 6))
        sns.heatmap(amt_pivot, cmap="Blues", annot=False, fmt=".0f", ax=ax)
        ax.set_title(f"{account_name} – Monthly Amount Heatmap")
        ax.set_ylabel("Year")
        ax.set_xlabel("Month")
        plt.tight_layout()
        fig.savefig(os.path.join(graphs_dir, f"{safe_name}_monthly_amount_heatmap.png"), dpi=160)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(11, 6))
        sns.heatmap(cnt_pivot, cmap="Greens", annot=False, fmt=".0f", ax=ax)
        ax.set_title(f"{account_name} – Monthly Order Count Heatmap")
        ax.set_ylabel("Year")
        ax.set_xlabel("Month")
        plt.tight_layout()
        fig.savefig(os.path.join(graphs_dir, f"{safe_name}_monthly_order_count_heatmap.png"), dpi=160)
        plt.close(fig)

    # Top categories (sum LineAmount per family)
    cdf = categories_df[categories_df["AccountName"] == account_name]
    if not cdf.empty:
        # Aggregate across years for a simple "top categories overall" view
        top = (
            cdf.groupby("ProductFamily", as_index=False)["LineAmount"].sum().sort_values("LineAmount", ascending=False)
        )
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(y="ProductFamily", x="LineAmount", data=top, ax=ax, color="#54A24B")
        ax.set_title(f"{account_name} – Top Product Categories (All Years)")
        ax.set_xlabel("Total Amount")
        ax.set_ylabel("Category")
        plt.tight_layout()
        fig.savefig(os.path.join(graphs_dir, f"{safe_name}_top_categories.png"), dpi=150)
        plt.close(fig)


def plot_combined_overview_graphs(graphs_dir: str, yearly_df: pd.DataFrame) -> None:
    if yearly_df.empty:
        return
    # Combined overview: each customer line over years
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=yearly_df, x="Year", y="TotalAmount", hue="AccountName", marker="o", ax=ax)
    ax.set_title("All Customers – Yearly Total Amount")
    ax.set_ylabel("Total Amount")
    ax.set_xlabel("Year")
    ax.legend(loc="best", fontsize="small", ncol=2)
    plt.tight_layout()
    fig.savefig(os.path.join(graphs_dir, "all_customers_yearly_total_amount.png"), dpi=160)
    plt.close(fig)


def run_analysis(customer_names: Optional[List[str]] = None) -> None:
    names = customer_names if customer_names else DEFAULT_CUSTOMER_NAMES
    base_dir = os.path.abspath(os.path.dirname(__file__))
    csv_dir, graphs_dir = ensure_output_dirs(base_dir)

    print("Loading Salesforce configuration from environment...")
    config = load_salesforce_config_from_env()

    print(f"Connecting to Salesforce (domain='{config.domain}')...")
    try:
        sf = connect_to_salesforce(config)
    except Exception as e:
        print(
            "Failed to connect to Salesforce.\n"
            "Tips: Set SF_DOMAIN to 'login' or 'test' for standard orgs, or to your My Domain subdomain only (e.g., 'rmfp'), not a full host like 'rmfp.salesforce.com'.\n"
            "You can also provide 'https://<mydomain>.my.salesforce.com' and it will be normalized."
        )
        print(f"Underlying error: {e}")
        return
    print("Connected.")

    print("Fetching Accounts by names...")
    accounts_df = fetch_accounts_by_names(sf, names)
    if accounts_df.empty:
        print("No matching Accounts found for the provided names. Exiting.")
        return
    print(f"Found {len(accounts_df)} accounts.")

    account_ids = accounts_df["Id"].tolist()

    print("Fetching Closed Won Opportunities...")
    opps_df = fetch_closed_won_opportunities(sf, account_ids)
    print(f"Fetched {len(opps_df)} opportunities.")

    print("Fetching Quote Line Items for product categories...")
    qli_df = fetch_quote_line_items_for_accounts(sf, account_ids)
    print(f"Fetched {len(qli_df)} quote line items.")

    print("Computing metrics...")
    yearly_df = compute_yearly_metrics(opps_df, accounts_df)
    monthly_df = compute_monthly_metrics(opps_df, accounts_df)
    categories_df = compute_top_categories(qli_df, accounts_df)

    print("Writing CSV outputs...")
    write_csvs(csv_dir, yearly_df, monthly_df, categories_df)
    # Excel workbook
    try:
        write_excel(csv_dir, yearly_df, monthly_df, categories_df)
    except Exception as e:
        print(f"Excel export failed: {e}")

    print("Generating graphs...")
    # Per-customer graphs
    for account_name in sorted(accounts_df["Name"].dropna().unique().tolist()):
        plot_per_customer_graphs(graphs_dir, account_name, yearly_df, monthly_df, categories_df)

    # Combined overview graphs
    plot_combined_overview_graphs(graphs_dir, yearly_df)

    print("Done. CSVs are in 'output/' and graphs in 'output/graphs/'.")


if __name__ == "__main__":
    # Optional: allow overriding customer names via a JSON array arg
    override_names: Optional[List[str]] = None
    if len(sys.argv) > 1:
        try:
            override_names = json.loads(sys.argv[1])
            if not isinstance(override_names, list):
                print("Argument must be a JSON array of names. Falling back to defaults.")
                override_names = None
        except Exception:
            print("Failed to parse argument as JSON list. Falling back to defaults.")
            override_names = None

    run_analysis(override_names)

