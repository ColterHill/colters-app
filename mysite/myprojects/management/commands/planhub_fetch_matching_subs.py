import os
import json
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from urllib.parse import urljoin


# ✅ Same target trades from earlier
TARGET_TRADES = set([
    "3rd Party Plan Room", "Architect", "Architectural Woodwork", "Fascia",
    "Fences and Gates", "Fencing and Gates", "Fiber-cement Siding", "Finish Carpentry",
    "FRP - Wall Panels", "Glued Laminated Timber", "Handrails and Railings",
    "Heavy Timber Construction", "Lumber Suppliers", "Material Estimating",
    "Preconstruction, Planning and Supervision", "Rough Carpentry and Wood Framing",
    "Sauna / Steam Rooms", "Stainless Steel Railings", "Steel Joists",
    "Stone and Stone Veneer Siding", "Vinyl Railings",
    "Wood and Plastic Restoration and Cleaning", "Wood Decking", "Wood Shake Shingles",
    "Wood Siding", "Wood Stairs / Railings", "Wood Truss Supplier"
])


class Command(BaseCommand):
    help = 'Fetch open projects and match subcontractors by target trades'

    def add_arguments(self, parser):
        parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
        parser.add_argument("--limit", type=int, default=5, help="Max number of open projects to process")

    def handle(self, *args, **options):
        start_date = options["start_date"] or datetime.now().strftime("%Y-%m-%d")
        end_date = options["end_date"] or datetime.now().strftime("%Y-%m-%d")
        limit = options["limit"]

        self.stdout.write(f"Fetching open projects updated since {start_date}...")

        projects = self.fetch_open_projects(start_date, end_date, limit)
        self.stdout.write(f"Found {len(projects)} open projects.")

        for project in projects:
            project_id = project['id']
            project_title = project['title']
            self.stdout.write(f"\n📁 Project: {project_title} (ID: {project_id})")

            subs = self.fetch_project_subs(project_id)

            if not subs:
                self.stdout.write("  No subcontractors found.")
                continue

            self.stdout.write(f"  Subcontractors: {len(subs)}")

            for sub in subs:
                company_id = sub.get("company_id")
                if not company_id:
                    continue
                profile = self.fetch_company_profile(company_id)
                if not profile:
                    continue

                trades = profile.get("company", {}).get("trades", [])
                matched = [t["name"] for t in trades if t["name"] in TARGET_TRADES]

                if matched:
                    general_info = profile["tabs"]["overview"]["general_information"]
                    sub_id = sub.get("uId")
                    email = general_info.get('email') or "N/A"
                    phone_data = general_info.get('phone')
                    if isinstance(phone_data, dict):
                        phone = phone_data.get('number')
                    else:
                        phone = phone_data if isinstance(phone_data, str) else "N/A"

                    self.stdout.write(f"\n✅ MATCH: {profile['company']['name']}")
                    self.stdout.write(f"    Sub ID: {sub_id}")
                    self.stdout.write(f"    Email: {email}")
                    self.stdout.write(f"    Phone: {phone}")
                    self.stdout.write(f"    Trades: {matched}")

    def fetch_open_projects(self, start_date, end_date, limit):
        url = 'https://openapi.planhub.com/api/v2/get-open-projects'
        headers = {
            'Authorization': os.getenv("PLANHUB_OPEN_API_KEY"),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        # Use start_date as updatedSince
        if start_date:
            updated_since = f"{start_date} 00:00:00"
        else:
            default_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            updated_since = f"{default_date} 00:00:00"

        payload = {
            "updatedSince": updated_since,
            "pageSize": limit,
            "cursor": ""
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("data", {}).get("listProjects", {}).get("data", [])
        except Exception as e:
            self.stderr.write(f"Error fetching open projects: {e}")
            return []

    def fetch_project_subs(self, project_id):
        auth_token = self.load_auth_token()
        url = "https://api.planhub.com/api/v1/getProjectActivityTrackerV2"
        headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Referer': 'https://supplier.planhub.com/',
            'Origin': 'https://supplier.planhub.com',
        }
        payload = {
            "biddingStatus": "",
            "limit": 5000,
            "orderBy": "desc",
            "pageNumber": 0,
            "projectId": int(project_id),
            "received_estimate": None,
            "searchByName": "",
            "sortedBy": "companyName",
            "subTrades": "",
            "view": "projectView"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json().get("data", {}).get("data", [])
        except Exception as e:
            self.stderr.write(f"Error fetching subs for project {project_id}: {e}")
            return []

    def fetch_company_profile(self, company_id):
        url = f"https://api.planhub.com/api/v1/company/{company_id}/profile"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get("result", {}).get("profile", {})
        except Exception as e:
            self.stderr.write(f"Error fetching profile for company {company_id}: {e}")
            return None

    def load_auth_token(self):
        try:
            with open("auth_token.json", "r") as f:
                return json.load(f).get("auth_token")
        except FileNotFoundError:
            raise ValueError("Auth token file not found. Please run `planhub_scraper_auth.py` first.")
