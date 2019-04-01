#!/usr/bin/env python3

# This script revokes users' key if there is no any activity during last 30 days. Or if key had been created more that 30 days ago and never used.
# as AWS recommends https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#rotating_access_keys_cli

import boto3
import datetime

resource = boto3.resource('iam')
client = boto3.client('iam')
today = datetime.date.today()
# Required inactivity threshold
threshold = datetime.timedelta(days=2)   # !!!!! Change to required thresholds
KEY = ''        # !!!!

for user in resource.users.all():
    print (user.user_name)      # debug
    Metadata = client.list_access_keys(UserName=user.user_name)
    if Metadata['AccessKeyMetadata']:
        # print(Metadata)     # debug
        for key in user.access_keys.all():
            # print (key.access_key_id)       # debug
            AccessId = key.access_key_id
            Status = key.status
            LastUsed = client.get_access_key_last_used(AccessKeyId=AccessId)
            # working with only active keys
            if (Status == "Active"):
                print ('Key is active:', AccessId)  # debug
                print(LastUsed['AccessKeyLastUsed'])        # debug
                # if KEY not in LastUsed['AccessKeyLastUsed']:
                #     print('Key is never used')
                #     creationDate = Metadata['AccessKeyMetadata'][0]['CreateDate'].date()
                #     print('Creation date:',creationDate)
                # else:
                lastUsedTimestamp = LastUsed['AccessKeyLastUsed'].get('LastUsedDate')
                last = lastUsedTimestamp.date()
                # # Check diff between lastUsedDate and today
                # inactiveDays = today - last
                # # print(inactiveDays.days)      # debug
                # if (inactiveDays > threshold):
                #     # print('Inactive days:', inactiveDays.days)      # debug
                #     deactivate = client.update_access_key(AccessKeyId=AccessId, Status='Inactive', UserName=user.user_name)
                #     # print(AccessId, ' key has been deactivated')    # debug
            else:
                print ('Key is inactive:', AccessId) 
                print(LastUsed['AccessKeyLastUsed']) 
