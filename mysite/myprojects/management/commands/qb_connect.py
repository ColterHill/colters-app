from django.core.management.base import BaseCommand
from intuitlib.client import AuthClient
from django.conf import settings

from django.core.management.base import BaseCommand
import requests

from myprojects.management.commands.test_bistrack_connect import access_token


class Command(BaseCommand):
    help = 'Fetches company info from the QuickBooks Sandbox API'

    def handle(self, *args, **kwargs):
        # Sandbox Credentials
        # company_id = '9341453603815096'
        # access_token = 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..iEGBM9-IbG0gfzdWMIxAkA.0uxvwzIcap49P5TSOJlAUoiFhTtE6C8IjFXc0i0B_bvXoYJpXS8NVluULmNw210Ud6qfjuIWZSmWaSgJPzcY9ZrhI5BqRY9tbbBcVUEyjGGfZpFxeakD1XpstFlw6DIp3STtlBzB1GEcEfso5stn-ui5KVru0Egzy68NiWZLJK9pS3O8Zo3nvWUf9Gv2tNqmZbqokGmhD8N60B_xQCggULcKT0w68bBbEp9ZyjOE9QwrFu2-klzO6_6rXvDCll1NIpbQGrSDa2ED9YM0PWxdzod6HhRUJB5ZYmoq3VljTaHUdxlgDJwzGyYr5_ThEdCVc5ADAvSL_8luFfV1kKUT0dSQSuJA1NpyWJ0GxvBU2kE7KXV2QgtU7zv54dR2GPZD4dYwD2BbfveMzFOvrYY6bLDhB6UFJFgH0PUz2IDI8SC09NvWvV3YQRoYUxLQlR_aplyI4DFBE3hlWu8Qc5qTaBZ04eJ4cgL7wYnwdqoJxcVUUKdCMrM4oE5F6citZzgP2AoiOoCP0VnRn-2wlNXEkgAxnSj06yR6MaRJfhDMbvpX4LgFnjkH8f-3fdAIErEIQ0jIhHrQKcmmXXQbdKokvc8aF6ySCmDdl_4Q8sYvOT_7yBXQV7igNnBi_-ohfuPBhVkyDfcrHTsFgYHlr4avrANIHAOJnxDhpV3iY2OTjNcoMDjoUiO9D-pJFc1ykQcRDGPPQ_DgP5lX4dWzHsTkDD-G08D-4E7pG0C749kpj_8K7NTkLIvi9dWdrrFw2mvJL2DYgWb0OLqx4DHOj-b3pvhQ7g1RN_rVh82LA4tu51e5mu_td1QBZ2Ak26e6M8tZQhOluo71SaTa7Ulp6RV4i5MuWwun_iyVoesno4KbvtIM8aCNzEcBIumO7Vs2-nlT.rfNjha7gUxRfvI8ep-KU3Q'

        # Production Credentials
        access_token = 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..W3XVDmOAd5r4KU2UPb3f0g.AaYPfz8afYN0fIl8rr9ce47HtTLh1xqWx1ToeccCV-ifPltToFCmrzVHlNRHSyjpEowea4HXX9kqxQndIFWSlSw3Z8ZHBP-rNIuaZJZRJbmQ8y8ot6vKuCD-4wp4gtwJiT1ApRq0SmVnkQGAJ6-7mQ13VOb8wonhECWsNzaFtGDXCZYZYqTQkdmGMN5eDU2WLyybl6CigrdoHB56aeoHUTKwjoKxm0MrXWYVjRNfvqcDB9h575kuw4I-FYz6S5YCMKdYTqpRxVW1dzCBerEB5wiEtFsy2VgtXP_NMXKKreOwS8FYSa_C37heMHu62FK6U1sHf_4SB9GxfUfs6y_IrY83kR816NRKt7GaGR7Th_cU84jGqeuk6GJ7EFcsjSEUupgHqt-0jBgczXsoa-ZHqp0aqcz_v5vyRy2ntM9IhdzRzgpl7GplAByaj5zCyD-ATzKfqcavASDLYsjRstIW-Q5W4Sby9WAa19GoDw0uzDoaB976JDIVPQSZ-lmYMeCVyvCoO_Xf0tU81OQXOAN-jqMVzjbROXmPrIOyI_EBkZsUng8eVMQrxT5sSDG0oXW2WsI61gODJtZYCzmp315m617HuukGlZoaKjNcTv0p1SVsZYbL_jMlngHZ_V5uk8jlAmTtCbaAwqpORu8q9N-NjfyTgCkzweONWzF7zZu99lG5OtPxSxHuvPnXHUaqOFBafKfx8taO_a7cvjkJX_DNvbG27nCzY7OLEe9JdjSTQLU9gC7-J6jGm7nuwFYWqfPlHFE4YAJL37BBXY_Zo49Xvm5O9GdR8lFCBZagcmeJtLm_TAzC37gCLeo9QXKiA3ZTNcmBvITI1OtaSRlSWW0kJeoPz4m6yjo5pKiEKC5nbsrT391O01TlO4KYJifTtJJx.PI3Y9F22KDuAPy-PyLR3FA'
        company_id = '9341453519021912'

        query = "SELECT * FROM Vendor"

        # Construct the URL using the company_id for both places in the URL
        url = (
            f'https://quickbooks.api.intuit.com/v3/company/'
            f'{company_id}/query?minorversion=65'
        )

        # Define the headers as used in the curl command
        headers = {
            'accept': 'application/json',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/text',
        }

        try:
            # Make the request with the query
            response = requests.post(url, headers=headers, data=query)
            response.raise_for_status()

            # Parse and print the response
            data = response.json()
            # self.stdout.write(f"Vendors: {data}")

            for vendor in data['QueryResponse']['Vendor']:
                # self.stdout.write(f"Vendor: {vendor}")
                company_name = vendor['CompanyName']
                balance = vendor['Balance']
                active = vendor['Active']
                if vendor['BillAddr']:
                    billing_address = vendor['BillAddr']
                else:
                    billing_address = "No Billing Address"
                vendor_id = vendor['Id']
                print(f"Company Name: {company_name} ID: {vendor_id} Balance: {balance} Active: {active}")
                print(f"Billing Address: {billing_address}")

        except requests.RequestException as e:
            self.stderr.write(f"Request failed: {e}")
