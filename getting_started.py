import json
import pandas
from simple_salesforce import Salesforce, SalesforceLogin, SFType

username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

sf = Salesforce(username=username, password=password, security_token=security_token)

metadata_org = sf.describe()
df_sobjects = pandas.DataFrame(metadata_org['sobjects'])
df_sobjects.to_csv('org metadata info.csv', index=False)

# access object info
# Method 1
account = sf.account
account_metadata = account.describe()

df_account_metadata = pandas.DataFrame(account_metadata.get('fields'))
df_account_metadata.to_csv('account object metadata.csv', index=False)


