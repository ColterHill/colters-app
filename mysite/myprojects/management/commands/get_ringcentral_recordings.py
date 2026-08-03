import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from ringcentral import SDK


class Command(BaseCommand):
    help = 'Fetch the 5 most recent call recordings from RingCentral'

    def add_arguments(self, parser):
        parser.add_argument(
            '--credentials',
            type=str,
            default='/Users/colterhill/Downloads/rc-credentials.json',
            help='Path to RingCentral credentials JSON file'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='Colter Hill',
            help='User name to get JWT token for (must match key in credentials file)'
        )
        parser.add_argument(
            '--download',
            action='store_true',
            help='Download recording files to local directory'
        )
        parser.add_argument(
            '--download-dir',
            type=str,
            default='./ringcentral_recordings',
            help='Directory to save downloaded recordings (default: ./ringcentral_recordings)'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Base URL for the Django server (for generating proxy URLs, default: http://localhost:8000)'
        )

    def handle(self, *args, **options):
        credentials_path = options['credentials']
        user_name = options['user']

        # Load credentials
        try:
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Credentials file not found: {credentials_path}')
            )
            return
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON in credentials file: {credentials_path}')
            )
            return

        # Extract credentials
        client_id = credentials.get('clientId')
        client_secret = credentials.get('clientSecret')
        server = credentials.get('server', 'https://platform.ringcentral.com')
        jwt_tokens = credentials.get('jwt', {})

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR('Missing clientId or clientSecret in credentials file')
            )
            return

        jwt_token = jwt_tokens.get(user_name)
        if not jwt_token:
            self.stdout.write(
                self.style.ERROR(
                    f'JWT token not found for user "{user_name}". '
                    f'Available users: {", ".join(jwt_tokens.keys())}'
                )
            )
            return

        # Initialize SDK
        sdk = SDK(client_id, client_secret, server)
        platform = sdk.platform()

        # Authenticate
        try:
            self.stdout.write('Authenticating with RingCentral...')
            platform.login(jwt=jwt_token)
            self.stdout.write(self.style.SUCCESS('✓ Authentication successful'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Authentication failed: {str(e)}')
            )
            return

        # Fetch call log with recordings
        try:
            self.stdout.write('\nFetching call recordings...')
            
            # Try account-level endpoint first with withRecording parameter
            # This is more likely to return recordings
            account_endpoint = '/restapi/v1.0/account/~/call-log'
            account_params = {
                'withRecording': 'True',
                'perPage': 5,
                'orderBy': 'startTime desc'
            }
            
            self.stdout.write('Trying account-level call log with withRecording=True...')
            response = platform.get(account_endpoint, query_params=account_params)
            result = response.json()

            # JsonObject uses attribute access, not dictionary methods
            records = getattr(result, 'records', [])
            
            if not records:
                self.stdout.write(
                    self.style.WARNING('\nNo calls found with account-level endpoint. Trying extension-level...')
                )
                # Fallback to extension-level endpoint
                extension_endpoint = '/restapi/v1.0/account/~/extension/~/call-log'
                extension_params = {
                    'withRecording': 'True',
                    'perPage': 20,
                    'orderBy': 'startTime desc'
                }
                response = platform.get(extension_endpoint, query_params=extension_params)
                result = response.json()
                records = getattr(result, 'records', [])
                
                if not records:
                    self.stdout.write(
                        self.style.WARNING('\nNo calls found. Trying without withRecording filter...')
                    )
                    # Try without withRecording to see if we get any calls
                    response2 = platform.get(extension_endpoint, query_params={'perPage': 10, 'orderBy': 'startTime desc'})
                    result2 = response2.json()
                    records2 = getattr(result2, 'records', [])
                    if records2:
                        self.stdout.write(f'Found {len(records2)} calls without withRecording filter')
                        records = records2
                    else:
                        self.stdout.write(
                            self.style.ERROR('\nNo calls found even without filters.')
                        )
                        return
            
            # Filter for calls that actually have recordings
            calls_with_recordings = []
            self.stdout.write(f'\nChecking {len(records)} calls for recordings...')
            
            for record in records:
                # Check if recording attribute exists
                recording = getattr(record, 'recording', None)
                if recording:
                    calls_with_recordings.append(record)
                else:
                    # Debug: show what attributes this call has
                    self.stdout.write(f'  Call {getattr(record, "id", "unknown")} has no recording attribute')
            
            if not calls_with_recordings:
                self.stdout.write(
                    self.style.WARNING(f'\nFound {len(records)} calls, but none have recordings attached.')
                )
                self.stdout.write('\nPossible reasons:')
                self.stdout.write('  1. Recordings may not be available yet (processing delay)')
                self.stdout.write('  2. API permissions may not include ReadCallRecordings')
                self.stdout.write('  3. Recordings may be disabled for these extensions')
                self.stdout.write('  4. The withRecording parameter may not be working as expected')
                
                # Show first call structure for debugging
                if records:
                    first_call = records[0]
                    self.stdout.write(f'\nFirst call structure:')
                    self.stdout.write(f'  ID: {getattr(first_call, "id", "N/A")}')
                    self.stdout.write(f'  Session ID: {getattr(first_call, "sessionId", "N/A")}')
                    self.stdout.write(f'  Start Time: {getattr(first_call, "startTime", "N/A")}')
                    self.stdout.write(f'  Attributes: {[attr for attr in dir(first_call) if not attr.startswith("_")][:15]}')
                return
            
            records = calls_with_recordings[:5]  # Limit to 5 most recent with recordings

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Found {len(records)} call recording(s)\n')
            )
            self.stdout.write('=' * 80)

            # Display recording information
            for idx, record in enumerate(records, 1):
                self.stdout.write(f'\nRecording #{idx}')
                self.stdout.write('-' * 80)
                
                # Basic call info
                direction = getattr(record, 'direction', 'N/A')
                action = getattr(record, 'action', 'N/A')
                result_type = getattr(record, 'result', 'N/A')
                
                self.stdout.write(f"Direction: {direction}")
                self.stdout.write(f"Action: {action}")
                self.stdout.write(f"Result: {result_type}")

                # Call participants
                from_info = getattr(record, 'from_', None) or getattr(record, 'from', None)
                to_info = getattr(record, 'to', None)
                
                if from_info:
                    from_name = getattr(from_info, 'name', 'N/A')
                    from_number = getattr(from_info, 'phoneNumber', 'N/A')
                else:
                    from_name = 'N/A'
                    from_number = 'N/A'
                
                if to_info:
                    to_name = getattr(to_info, 'name', 'N/A')
                    to_number = getattr(to_info, 'phoneNumber', 'N/A')
                else:
                    to_name = 'N/A'
                    to_number = 'N/A'
                
                self.stdout.write(f"\nFrom: {from_name} ({from_number})")
                self.stdout.write(f"To: {to_name} ({to_number})")

                # Call timing
                start_time = getattr(record, 'startTime', 'N/A')
                duration = getattr(record, 'duration', 'N/A')
                
                self.stdout.write(f"\nStart Time: {start_time}")
                self.stdout.write(f"Duration: {duration} seconds")

                # Recording info
                recording = getattr(record, 'recording', None)
                if recording:
                    recording_id = getattr(recording, 'id', 'N/A')
                    recording_type = getattr(recording, 'type', 'N/A')
                    content_type = getattr(recording, 'contentType', 'N/A')
                    content_uri = getattr(recording, 'contentUri', 'N/A')
                    duration_seconds = getattr(recording, 'duration', 'N/A')
                    
                    self.stdout.write(f"\nRecording ID: {recording_id}")
                    self.stdout.write(f"Recording Type: {recording_type}")
                    self.stdout.write(f"Duration: {duration_seconds} seconds")
                    
                    # Display the content URI prominently
                    if content_uri and content_uri != 'N/A':
                        # Generate local proxy URL that works in browser
                        base_url = options.get('base_url', 'http://localhost:8000')
                        local_url = f"{base_url}/ringcentral/recording/{recording_id}/"
                        
                        self.stdout.write(f"\n{self.style.SUCCESS('🎵 Listen to Recording (Browser):')}")
                        self.stdout.write(f"   {local_url}")
                        self.stdout.write(f"\n{self.style.WARNING('   (Direct RingCentral URL requires auth):')}")
                        self.stdout.write(f"   {content_uri}")
                        
                        # If download option is enabled, download the file
                        if options.get('download'):
                            try:
                                # Extract the path from the full URL for the API call
                                # content_uri can be:
                                # - Full URL: https://media.ringcentral.com/restapi/v1.0/account/.../recording/.../content
                                # - Relative path: /restapi/v1.0/account/.../recording/.../content
                                
                                if content_uri.startswith('/restapi/'):
                                    # Already a relative path
                                    recording_path = content_uri
                                elif 'media.ringcentral.com' in content_uri or 'platform.ringcentral.com' in content_uri:
                                    # Extract the path from full URL
                                    path_start = content_uri.find('/restapi/')
                                    if path_start != -1:
                                        recording_path = content_uri[path_start:]
                                    else:
                                        raise ValueError(f"Could not extract path from URI: {content_uri}")
                                else:
                                    raise ValueError(f"Unexpected URI format: {content_uri}")
                                
                                if recording_path:
                                    # Create download directory if it doesn't exist
                                    download_dir = options.get('download_dir', './ringcentral_recordings')
                                    os.makedirs(download_dir, exist_ok=True)
                                    
                                    # Generate filename from call info
                                    # Parse date from ISO format: 2025-12-05T17:25:28.344Z
                                    if start_time != 'N/A' and 'T' in start_time:
                                        try:
                                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                            date_str = dt.strftime('%Y%m%d_%H%M%S')
                                        except:
                                            date_str = start_time.replace(':', '-').replace('.', '-')[:19]
                                    else:
                                        date_str = 'unknown'
                                    
                                    from_clean = from_number.replace('+', '').replace(' ', '').replace('-', '') if from_number != 'N/A' else 'unknown'
                                    to_clean = to_number.replace('+', '').replace(' ', '').replace('-', '') if to_number != 'N/A' else 'unknown'
                                    
                                    # Clean names for filename
                                    from_name_clean = from_name.replace(' ', '_').replace('/', '_')[:20] if from_name != 'N/A' else 'unknown'
                                    to_name_clean = to_name.replace(' ', '_').replace('/', '_')[:20] if to_name != 'N/A' else 'unknown'
                                    
                                    filename = f"{date_str}_{from_name_clean}_{from_clean}_to_{to_name_clean}_{to_clean}_{recording_id}.mp3"
                                    # Remove any invalid filename characters
                                    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
                                    filepath = os.path.join(download_dir, filename)
                                    
                                    # Download the recording
                                    self.stdout.write(f"   Downloading to: {filepath}...")
                                    rec_response = platform.get(recording_path)
                                    
                                    # Get the binary content
                                    recording_content = rec_response.body()
                                    
                                    # Save to file
                                    with open(filepath, 'wb') as f:
                                        f.write(recording_content)
                                    
                                    file_size = os.path.getsize(filepath)
                                    self.stdout.write(
                                        self.style.SUCCESS(f"   ✓ Downloaded ({file_size:,} bytes)")
                                    )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f"   ✗ Download failed: {str(e)}")
                                )
                    else:
                        self.stdout.write(self.style.WARNING("\nNo content URI available"))
                else:
                    self.stdout.write(self.style.WARNING("\nNo recording data available"))

                self.stdout.write('')

            self.stdout.write('=' * 80)
            self.stdout.write(self.style.SUCCESS('\n✓ Complete'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError fetching call recordings: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())

