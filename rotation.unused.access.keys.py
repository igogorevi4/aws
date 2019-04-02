#!/usr/bin/env python3

# This script revokes users' key if there is no any activity during last 30 days. Or if key had been created more that 30 days ago and never used.
# as AWS recommends https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#rotating_access_keys_cli
# Run in AWS Lambda by schedule (CloudWatch Event) https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLambdaSchedule.html 

import boto3
import datetime

resource = boto3.resource('iam')
client = boto3.client('iam')
today = datetime.date.today()
# Required inactivity threshold. Change to required thresholds
threshold = datetime.timedelta(days=1)
# some trick to get keys that are never used
notAvaiableKey = 'N/A'

for user in resource.users.all():
    Metadata = client.list_access_keys(UserName=user.user_name)
    if Metadata['AccessKeyMetadata']:
        for key in user.access_keys.all():
            AccessId = key.access_key_id
            Status = key.status
            LastUsed = client.get_access_key_last_used(AccessKeyId=AccessId)
            # notice only active keys
            if (Status == "Active"):
                # check if key is never used
                if (notAvaiableKey in LastUsed['AccessKeyLastUsed']['ServiceName']):
                    creationDate = Metadata['AccessKeyMetadata'][0]['CreateDate'].date()
                    unsedDays = today - creationDate
                    if (unsedDays >= threshold):
                        # Deactivating key
                        client.update_access_key(AccessKeyId=AccessId, Status='Inactive', UserName=user.user_name)
                # else check its last used date
                else:
                    lastUsedTimestamp = LastUsed['AccessKeyLastUsed'].get('LastUsedDate')
                    last = lastUsedTimestamp.date()
                    inactiveDays = today - last
                    if (inactiveDays >= threshold):
                        # Deactivating key
                        deactivating = client.update_access_key(AccessKeyId=AccessId, Status='Inactive', UserName=user.user_name)
            else:
                print('Key is inactive:', AccessId)