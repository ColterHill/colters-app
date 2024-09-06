import json
import pandas as pd
from simple_salesforce import Salesforce, SalesforceLogin, SFType

username = 'chill@rmfp.com'
password = 'RMFP2023a!'
security_token = '4knV7IDiRmbtIqkFU4XEzzoMi'
domain = 'rmfp.salesforce.com'

sf = Salesforce(username=username, password=password, security_token=security_token)


group_members = sf.query_all("SELECT GroupID,UserOrGroupId FROM GroupMember")
active_users = sf.query_all("SELECT Username,Name,Id FROM User WHERE isActive = True")
groups = sf.query_all("SELECT Id,Name,Type from Group")

group_members_df = pd.DataFrame(group_members['records'])

users_df = pd.DataFrame(active_users['records'])
users_df = users_df.drop(columns=['attributes'])

groups_df = pd.DataFrame(groups['records'])
groups_df = groups_df.drop(columns=['attributes'])


def get_user_name(user_id):
    for index, name in users_df.iterrows():
        if user_id == name['Id']:
            print("/t" + name['Name'])

def get_members(group_id):
    result = group_members_df.loc[group_members_df['GroupId'] == group_id]
    for index, member in result.iterrows():
        get_user_name(["UserOrGroupId"])

def get_groups_with_users():
    for index, group in groups_df.iterrows():
        group_id = group['Id']
        group_name = group['Name']
        print(str(group_name)+":")
        get_members(group_id)


get_groups_with_users()