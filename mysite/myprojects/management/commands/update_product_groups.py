from django.core.management.base import BaseCommand
from simple_salesforce import Salesforce
import pandas as pd

username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

salesforce = Salesforce(username=username, password=password, security_token=security_token)


class Command(BaseCommand):
    def handle(self, *args, **options):
        update_sf_product_list = []

        # Load CSV once outside the loop.
        csv_path = '/Users/colterhill/Documents/Data/Product data for dataloader/Products with Product Groups.csv'
        df = pd.read_csv(csv_path)

        # Build a mapping from product code to product group details.
        product_group_mapping = {}
        for row in df.itertuples():
            product_code = row._1  # Adjust based on your CSV column positions
            pg_lvl1 = row._3
            pg_lvl2 = row._4
            # Assuming one set of groups per product code; if multiple exist, decide which to use.
            product_group_mapping[product_code] = (pg_lvl1, pg_lvl2)

        # Query Salesforce for active products.
        sf_product_list_raw = salesforce.query_all(
            "SELECT Id, bistrack_product_code__c FROM Product2 WHERE IsActive = True AND bistrack_product_code__c != null"
        )
        sf_product_list = sf_product_list_raw['records']

        # Iterate over each Salesforce product.
        for product in sf_product_list:
            sf_product_id = product['Id']
            sf_product_code = product['bistrack_product_code__c']

            # Check if there's a matching product code in the CSV mapping.
            if sf_product_code in product_group_mapping:
                pg_lvl1, pg_lvl2 = product_group_mapping[sf_product_code]
                print(
                    f"Updating Salesforce Product ID: {sf_product_id} (Code: {sf_product_code}) with PG LVL1: {pg_lvl1} and PG LVL2: {pg_lvl2}")
                # Prepare update dictionary.
                sf_update_dict = {
                    'Id': sf_product_id,
                    'Category__c': pg_lvl1,
                    'SubCategory__c': pg_lvl2
                }
                update_sf_product_list.append(sf_update_dict)
            else:
                print(f"No matching CSV product found for Salesforce product code: {sf_product_code}")

        # If you have updates, perform a bulk update on Product2.
        if update_sf_product_list:
            resp = salesforce.bulk.Product2.update(update_sf_product_list, batch_size=10000, use_serial=True)
            print("Bulk update response:", resp)
            print("Number of records updated:", len(update_sf_product_list))
        else:
            print("No records to update.")
