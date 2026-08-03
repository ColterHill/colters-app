from django.core.management.base import BaseCommand
import requests
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Test CallRail API connection and pull session-specific attribution data'
    
    def handle(self, *args, **options):
        # Your API Key
        API_KEY = "477ac881b043df62d5b0d7104db1fbd2"
        ACCOUNT_ID = "227527750"

        # Specify which fields you want from the API
        fields = ",".join([
            "tracking_phone_number", "source_name", "customer_phone_number",
            "recording_player", "start_time", "keywords", "source",
            "utm_source", "utm_medium", "utm_campaign", "utm_content",
            "landing_page_url", "referring_url", "campaign", "transcription",
            "speaker_percent", "sentiment", "prior_calls", "gclid", "call_summary",
            "duration", "recording", "voicemail", "answered", "business_phone_number",
            "customer_city", "customer_country", "customer_name", "customer_state",
            "direction", "id", "recording_duration", "tracker_id", "medium",
            "referrer_domain", "last_requested_url", "keywords_spotted", "milestones",
            "device_type", "total_calls"
        ])
        
        url = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}/calls.json?fields={fields}"

        # Headers
        headers = {
            "Authorization": f"Token token={API_KEY}",
            "Content-Type": "application/json"
        }

        # Get calls from the last 30 days to test with recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            "page": 1, 
            "per_page": 10,  # Just get 10 calls for testing
            "start_date": start_date.strftime("%Y-%m-%d"), 
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        self.stdout.write(self.style.SUCCESS(f"\nFetching calls from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...\n"))
        
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            calls = data.get('calls', [])
            
            self.stdout.write(self.style.SUCCESS(f"Found {len(calls)} calls\n"))
            self.stdout.write("="*100 + "\n")
            
            for idx, call in enumerate(calls, 1):
                self.stdout.write(f"\n{'='*100}")
                self.stdout.write(f"CALL #{idx}")
                self.stdout.write(f"{'='*100}\n")
                
                # BASIC CALL INFO
                self.stdout.write(self.style.WARNING("BASIC CALL INFO:"))
                self.stdout.write(f"  Call Date: {call.get('start_time', 'N/A')}")
                self.stdout.write(f"  Customer #: {call.get('customer_phone_number', 'N/A')}")
                self.stdout.write(f"  Tracking # Called: {call.get('tracking_phone_number', 'N/A')}")
                self.stdout.write(f"  Duration: {call.get('duration', 'N/A')} seconds")
                self.stdout.write(f"  Recording: {'Yes' if call.get('recording') else 'No'}")
                
                # CHECK IF VISITOR SESSION DATA EXISTS IN CALL OBJECT
                has_session_data = call.get('landing_page_url') or call.get('referring_url') or call.get('utm_source')
                
                if has_session_data:
                    self.stdout.write(f"\n{self.style.SUCCESS('✅ VISITOR SESSION DATA (from call object):')}")
                    self.stdout.write(f"  Landing Page: {call.get('landing_page_url', 'N/A')}")
                    self.stdout.write(f"  Referring URL: {call.get('referring_url', 'N/A')}")
                    self.stdout.write(f"  Referrer Domain: {call.get('referrer_domain', 'N/A')}")
                    self.stdout.write(f"  Last Requested URL: {call.get('last_requested_url', 'N/A')}")
                    
                    self.stdout.write(f"\n  {self.style.SUCCESS('Source & Medium:')}")
                    self.stdout.write(f"    Source: {call.get('source', 'N/A')}")
                    self.stdout.write(f"    Medium: {call.get('medium', 'N/A')}")
                    self.stdout.write(f"    Campaign: {call.get('campaign', 'N/A')}")
                    
                    self.stdout.write(f"\n  {self.style.SUCCESS('UTM Parameters:')}")
                    self.stdout.write(f"    UTM Source: {call.get('utm_source', 'N/A')}")
                    self.stdout.write(f"    UTM Medium: {call.get('utm_medium', 'N/A')}")
                    self.stdout.write(f"    UTM Campaign: {call.get('utm_campaign', 'N/A')}")
                    self.stdout.write(f"    UTM Content: {call.get('utm_content', 'N/A')}")
                    
                    self.stdout.write(f"\n  {self.style.SUCCESS('Keywords:')}")
                    self.stdout.write(f"    Keywords: {call.get('keywords', 'N/A')}")
                    self.stdout.write(f"    Keywords Spotted: {call.get('keywords_spotted', 'N/A')}")
                else:
                    self.stdout.write(f"\n{self.style.ERROR('❌ NO VISITOR SESSION DATA')}")
                    self.stdout.write("  This caller did NOT visit your website before calling.")
                    self.stdout.write("  They called directly (e.g., from a Google Business Profile, saved number, etc.)")
                
                # TRACKING NUMBER ATTRIBUTION (may differ from session data)
                self.stdout.write(f"\n{self.style.WARNING('TRACKING NUMBER ATTRIBUTION:')}")
                self.stdout.write(f"  Source Name: {call.get('source_name', 'N/A')}")
                self.stdout.write(f"  Tracker ID: {call.get('tracker_id', 'N/A')}")
                
                # CALLER HISTORY
                self.stdout.write(f"\n{self.style.WARNING('CALLER HISTORY:')}")
                self.stdout.write(f"  Prior Calls: {call.get('prior_calls', 0)}")
                self.stdout.write(f"  Total Calls: {call.get('total_calls', 'N/A')}")
                
                # DEVICE INFO
                self.stdout.write(f"\n{self.style.WARNING('DEVICE INFO:')}")
                self.stdout.write(f"  Device Type: {call.get('device_type', 'N/A')}")
                self.stdout.write(f"  Last Requested URL: {call.get('last_requested_url', 'N/A')}")
                
                # MILESTONES DATA (First Touch & Last Touch Attribution)
                self.stdout.write(f"\n{self.style.SUCCESS('MILESTONES DATA (Attribution):')}")
                milestones = call.get('milestones', None)
                
                if milestones:
                    # FIRST TOUCH ATTRIBUTION
                    first_touch = milestones.get('first_touch')
                    if first_touch:
                        self.stdout.write(f"\n  {self.style.SUCCESS('FIRST TOUCH (First Time They Found You):')}")
                        self.stdout.write(f"    Event Date: {first_touch.get('event_date', 'N/A')}")
                        self.stdout.write(f"    Source: {first_touch.get('source', 'N/A')}")
                        self.stdout.write(f"    Medium: {first_touch.get('medium', 'N/A')}")
                        self.stdout.write(f"    Campaign: {first_touch.get('campaign', 'N/A')}")
                        self.stdout.write(f"    Landing Page: {first_touch.get('landing', 'N/A')}")
                        self.stdout.write(f"    Device: {first_touch.get('device', 'N/A')}")
                        self.stdout.write(f"    Browser: {first_touch.get('session_browser', 'N/A')}")
                        self.stdout.write(f"    Keywords: {first_touch.get('keywords', 'N/A')}")
                    
                    # LAST TOUCH ATTRIBUTION (This is what you want!)
                    last_touch = milestones.get('last_touch')
                    if last_touch:
                        self.stdout.write(f"\n  {self.style.SUCCESS('LAST TOUCH (Most Recent Interaction Before Call):')}")
                        self.stdout.write(f"    Event Date: {last_touch.get('event_date', 'N/A')}")
                        self.stdout.write(f"    Source: {last_touch.get('source', 'N/A')}")
                        self.stdout.write(f"    Medium: {last_touch.get('medium', 'N/A')}")
                        self.stdout.write(f"    Campaign: {last_touch.get('campaign', 'N/A')}")
                        self.stdout.write(f"    Landing Page: {last_touch.get('landing', 'N/A')}")
                        self.stdout.write(f"    Device: {last_touch.get('device', 'N/A')}")
                        self.stdout.write(f"    Browser: {last_touch.get('session_browser', 'N/A')}")
                        self.stdout.write(f"    Keywords: {last_touch.get('keywords', 'N/A')}")
                        
                        # UTM Parameters from last touch
                        url_utm_params = last_touch.get('url_utm_params', {})
                        if url_utm_params:
                            self.stdout.write(f"    UTM Source: {url_utm_params.get('utm_source', 'N/A')}")
                            self.stdout.write(f"    UTM Medium: {url_utm_params.get('utm_medium', 'N/A')}")
                            self.stdout.write(f"    UTM Campaign: {url_utm_params.get('utm_campaign', 'N/A')}")
                            self.stdout.write(f"    UTM Term: {url_utm_params.get('utm_term', 'N/A')}")
                    
                    # LEAD CREATED ATTRIBUTION
                    lead_created = milestones.get('lead_created')
                    if lead_created:
                        self.stdout.write(f"\n  {self.style.SUCCESS('LEAD CREATED (When Lead Was Created):')}")
                        self.stdout.write(f"    Event Date: {lead_created.get('event_date', 'N/A')}")
                        self.stdout.write(f"    Source: {lead_created.get('source', 'N/A')}")
                        self.stdout.write(f"    Medium: {lead_created.get('medium', 'N/A')}")
                        self.stdout.write(f"    Campaign: {lead_created.get('campaign', 'N/A')}")
                else:
                    self.stdout.write(f"  No milestone data available")
                
                # FULL CALL OBJECT (for debugging)
                self.stdout.write(f"\n{self.style.WARNING('Full Call Object (for debugging):')}")
                self.stdout.write(str(call))
                self.stdout.write("\n")
                
                # Only show first 3 calls for testing
                if idx >= 3:
                    break
                    
        else:
            self.stdout.write(self.style.ERROR(f"Error {response.status_code}: {response.text}"))