from django.core.management.base import BaseCommand
from datetime import datetime
import pandas as pd
from myprojects.models import EnneagramCode, EnneagramTest
from django.utils import timezone

class Command(BaseCommand):
    help = 'Uploads Enneagram test data from a CSV file'

    def handle(self, *args, **options):
        uploaded_file_name = 'Enneagram_codes.csv'
        csv_path = f'/Users/colterhill/Documents/Data/{uploaded_file_name}'

        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            self.stderr.write(f"File not found: {csv_path}")
            return

        df = df.reset_index()

        for row in df.itertuples():
            try:
                test_code = row._2
                order_number = row._5
                first_name = row._6
                last_name = row._7
                tester_email = row._8
                expiration_date = row._9
                used_on = row._10  # "Used on" column

                # Parse expiration date
                if isinstance(expiration_date, str):
                    expiration_date_obj = datetime.strptime(expiration_date.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
                else:
                    self.stderr.write(f"Skipping row {row.Index}: invalid expiration date")
                    continue

                # Determine status and used_date_obj
                if isinstance(used_on, str) and used_on.strip() == 'EXPIRED':
                    status = 2  # expired
                    used_date_obj = None
                elif isinstance(used_on, str):
                    used_date_obj = datetime.strptime(used_on.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").date()
                    status = 3  # complete
                else:
                    self.stderr.write(f"Skipping row {row.Index}: invalid 'Used on' value")
                    continue

                # Create or update EnneagramCode
                enneagram_code, is_new = EnneagramCode.objects.get_or_create(
                    code=test_code,
                    defaults={
                        'status': status,
                        'expiration': expiration_date_obj,
                    }
                )

                if not is_new:
                    enneagram_code.status = status
                    enneagram_code.expiration = expiration_date_obj
                    enneagram_code.save(update_fields=['status', 'expiration'])

                # Only create EnneagramTest if status is 'complete'
                if status == 3:
                    fullname = f"{first_name} {last_name}".strip()
                    EnneagramTest.objects.get_or_create(
                        email=tester_email,
                        enneagram_code=enneagram_code,
                        defaults={
                            'order_number': order_number,
                            'test_taken_date': used_date_obj,
                            'fullname': fullname,
                            'status': '1'
                        }
                    )

                self.stdout.write(f"✓ {test_code}: {'expired' if status == 2 else 'complete'}")

            except Exception as e:
                self.stderr.write(f"Error processing row {row.Index}: {e}")
