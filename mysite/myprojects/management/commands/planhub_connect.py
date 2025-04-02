import requests
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fetch open projects from Planhub API'

    def handle(self, *args, **options):
        url = 'https://openapi.planhub.com/api/v2/get-open-projects'
        headers = {
            'Authorization': '4D8Dc3ksLkzBFEAcex8hO4ea4SqH6DUQl0pJobXqVM9rpuUeHpQxJKyIVLAb3f0fQWdyR16hFjpWSCQQhcDK763ZEmLlfLE5Q7hThCCcx7CRtySfYBgeS9vEzs7KWSCacXSpEGJM5mK3SU7UJIv2DoxW2WSJO2ECGgiw4BAteU2fO5JIfOjAozp9cSShHdGV5VW5bSE6ZYraHq141EIMMF3BsT',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        payload = {
            "updatedSince": "2024-12-17 13:14:34",
            "pageSize": 1,
            "cursor": ""
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(f"Error fetching projects: {e}")
            return

        data = response.json()
        data_dig = data['data']
        project_data = data_dig['listProjects']
        projects = project_data['data']

        print(projects)

        # row_count = 0
        # for project in projects:
        #     project_id = project['id']
        #     project_name = project['title']
        #     created = project['created_at']
        #     details = project['details']
        #     start_date = project['start_date']
        #     end_date = project['end_date']
        #     posted_date = project['posted_date']
        #     maximum_value = project['maximum_value']
        #     stage = project['stage']
        #     special_instructions = project['special_instructions']
        #     merged_project_id = project['merged_project_id']
        #     active = project['is_active']
        #     address = project['address'] # List
        #     subtrades = project['subtrades'] #List
        #     trades = project['trades'] #List
        #     project_details_url = project['project_details_url']
        #     companies = project['companies'] # List
        #     types = project['types']
        #     subtypes = project['subtypes']
        #     sectors = project['sectors']
        #
        #     # Listing Contact info
        #     # for company in companies:
        #     #     contact_info = company['primary_contact']
        #     #     for info in contact_info:
        #     #         name = info[2]
        #     #         email_address = info[1]
        #     #         phone_number = info[3]
        #
        #
        #
        #     print(f"{project_id}: {project_name}")
        #     row_count += 1
        # print(row_count)
