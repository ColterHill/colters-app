import os
import sys
from typing import Dict, List, Optional

import pandas as pd
from simple_salesforce import Salesforce
from dotenv import load_dotenv


DEFAULT_CUSTOMER_NAMES: List[str] = [
    "Ned Avery", "Stevie Tuck / Andrew Scofield", "Nate Barrett", "John Clemmons",
    "Wes Gough", "Marcus Dickey", "Vladan Panic", "Andrew Bracken", "Jason Oleary",
    "Tim Perri", "Mark DeVos", "Ulises Tajonar-Diaz", "O'banyon Custer", "Cory Gill",
    "Ron L Hurtado", "Jesus Montelongo", "Brad Sanders", "Joe Thede", "Jason Ingalsbe",
    "Graciano Jimenez", "Jesus Dominguez",
]


def load_salesforce_config_from_env():
    load_dotenv()
    username = os.getenv("SF_USERNAME", "").strip()
    password = os.getenv("SF_PASSWORD", "").strip()
    token = os.getenv("SF_SECURITY_TOKEN", "").strip()
    domain_raw = os.getenv("SF_DOMAIN", "login").strip() or "login"
    
    # Normalize domain
    v = domain_raw.lower()
    if v.startswith("http://"):
        v = v[len("http://"):]
    elif v.startswith("https://"):
        v = v[len("https://"):]
    if v.endswith("/"):
        v = v[:-1]
    for suffix in [".my.salesforce.com", ".salesforce.com"]:
        if v.endswith(suffix):
            v = v[: -len(suffix)]
            break
    if v in ("login", "test"):
        domain = v
    elif v and not v.endswith(".my"):
        domain = f"{v}.my"
    else:
        domain = v or "login"

    missing = []
    if not username:
        missing.append("SF_USERNAME")
    if not password:
        missing.append("SF_PASSWORD")
    if not token:
        missing.append("SF_SECURITY_TOKEN")
    if missing:
        raise RuntimeError(f"Missing: {', '.join(missing)}")

    return username, password, token, domain


def connect_to_salesforce(username: str, password: str, token: str, domain: str):
    return Salesforce(
        username=username,
        password=password,
        security_token=token,
        domain=domain,
        client_id="ColtersAppMarketingAnalysis/1.0",
    )


def chunk_list(values: List[str], chunk_size: int) -> List[List[str]]:
    return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]


def query_all_records(sf: Salesforce, soql: str) -> List[Dict[str, object]]:
    result = sf.query(soql)
    records = list(result.get("records", []))
    while not result.get("done", True):
        next_url = result.get("nextRecordsUrl")
        if not next_url:
            break
        result = sf.query_more(next_url, identifier_is_url=True)
        records.extend(result.get("records", []))
    return records


def fetch_accounts_by_names(sf: Salesforce, account_names: List[str]) -> pd.DataFrame:
    if not account_names:
        return pd.DataFrame(columns=["Id", "Name"])

    all_rows = []
    for name_chunk in chunk_list(account_names, 50):
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


def fetch_quote_line_items_for_accounts(sf: Salesforce, account_ids: List[str]) -> pd.DataFrame:
    if not account_ids:
        return pd.DataFrame(columns=[
            "Id", "Quantity", "UnitPrice", "Category", "SubCategory", "ProductName", "OpportunityAccountId"
        ])

    all_rows = []
    for id_chunk in chunk_list(account_ids, 100):
        in_clause = ",".join([f"'{i}'" for i in id_chunk])
        soql = f"""
            SELECT Id,
                   Quantity,
                   UnitPrice,
                   PricebookEntry.Product2.Category__c,
                   PricebookEntry.Product2.SubCategory__c,
                   PricebookEntry.Product2.Name,
                   Quote.Opportunity.AccountId,
                   Quote.Opportunity.IsWon
            FROM QuoteLineItem
            WHERE Quote.Opportunity.AccountId IN ({in_clause})
        """
        for rec in query_all_records(sf, soql):
            category = None
            subcategory = None
            product_name = None
            try:
                category = (
                    rec.get("PricebookEntry", {})
                    .get("Product2", {})
                    .get("Category__c")
                )
                subcategory = (
                    rec.get("PricebookEntry", {})
                    .get("Product2", {})
                    .get("SubCategory__c")
                )
                product_name = (
                    rec.get("PricebookEntry", {})
                    .get("Product2", {})
                    .get("Name")
                )
            except Exception:
                pass

            opp = rec.get("Quote", {}).get("Opportunity", {})

            all_rows.append({
                "Id": rec.get("Id"),
                "Quantity": rec.get("Quantity"),
                "UnitPrice": rec.get("UnitPrice"),
                "Category": category,
                "SubCategory": subcategory,
                "ProductName": product_name,
                "OpportunityAccountId": opp.get("AccountId"),
                "OpportunityIsWon": opp.get("IsWon"),
            })

    df = pd.DataFrame(all_rows)
    if not df.empty:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0.0)
        df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0.0)
        df["LineAmount"] = df["Quantity"] * df["UnitPrice"]
        # Only keep won Opp line items
        df = df[df["OpportunityIsWon"] == True]
        # Fill missing product names/categories
        df["Category"] = df["Category"].fillna("Unspecified")
        df["SubCategory"] = df["SubCategory"].fillna("Unspecified")
        df["ProductName"] = df["ProductName"].fillna("Unknown Product")
        
        # Filter out unwanted product types
        df = df[
            ~df["ProductName"].str.contains("SPECIAL ORDER", case=False, na=False) &
            ~df["ProductName"].str.contains("DELIVERY", case=False, na=False) &
            ~df["ProductName"].str.contains("LINE ITEM", case=False, na=False)
        ]
    return df


def compute_top_products(qli_df: pd.DataFrame, accounts_df: pd.DataFrame) -> pd.DataFrame:
    if qli_df.empty or accounts_df.empty:
        return pd.DataFrame(columns=[
            "AccountId", "AccountName", "Rank", "ProductName", "Category", "SubCategory", "TotalAmount", "TotalQuantity"
        ])

    account_id_to_name = dict(zip(accounts_df["Id"], accounts_df["Name"]))
    
    # Group by Account and Product, sum amounts and quantities
    product_totals = qli_df.groupby(["OpportunityAccountId", "ProductName", "Category", "SubCategory"], as_index=False).agg(
        TotalAmount=("LineAmount", "sum"),
        TotalQuantity=("Quantity", "sum"),
    )
    
    # Find top 3 products for each account
    top_products = []
    for account_id in product_totals["OpportunityAccountId"].unique():
        account_data = product_totals[product_totals["OpportunityAccountId"] == account_id]
        # Sort by amount descending and take top 3
        top_3 = account_data.nlargest(3, "TotalAmount")
        
        for rank, (_, row) in enumerate(top_3.iterrows(), 1):
            top_products.append({
                "AccountId": account_id,
                "AccountName": account_id_to_name.get(account_id, "Unknown"),
                "Rank": rank,
                "ProductName": row["ProductName"],
                "Category": row["Category"],
                "SubCategory": row["SubCategory"],
                "TotalAmount": row["TotalAmount"],
                "TotalQuantity": row["TotalQuantity"],
            })
    
    result_df = pd.DataFrame(top_products)
    return result_df.sort_values(["AccountName", "Rank"]).reset_index(drop=True)


def main():
    names = DEFAULT_CUSTOMER_NAMES
    if len(sys.argv) > 1:
        try:
            import json
            override_names = json.loads(sys.argv[1])
            if isinstance(override_names, list):
                names = override_names
        except:
            pass

    print("Loading Salesforce configuration...")
    username, password, token, domain = load_salesforce_config_from_env()

    print(f"Connecting to Salesforce (domain='{domain}')...")
    try:
        sf = connect_to_salesforce(username, password, token, domain)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    print("Connected.")

    print("Fetching Accounts...")
    accounts_df = fetch_accounts_by_names(sf, names)
    if accounts_df.empty:
        print("No matching Accounts found.")
        return
    print(f"Found {len(accounts_df)} accounts.")

    account_ids = accounts_df["Id"].tolist()

    print("Fetching Quote Line Items...")
    qli_df = fetch_quote_line_items_for_accounts(sf, account_ids)
    print(f"Fetched {len(qli_df)} quote line items.")

    print("Computing top 3 products...")
    result_df = compute_top_products(qli_df, accounts_df)

    output_dir = "/Users/colterhill/Documents/Marketing/Salesforce Top Contractor data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "top_products.csv")
    result_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main() 