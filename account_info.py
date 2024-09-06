import json
import pandas as pd
from simple_salesforce import Salesforce, SalesforceLogin, SFType

username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

sf = Salesforce(username=username, password=password, security_token=security_token)

test_account_raw = sf.query("SELECT Id, Name FROM Account WHERE FirstName = 'Colter'")
test_account_list = test_account_raw['records']
test_account_dict = test_account_list[0]


def print_account_names_ids():
    for account in test_account_list:
        account_name = account['Name']
        account_id = account['Id']
        print("Name: " + account_name + "ID :" + account_id)

print_account_names_ids()