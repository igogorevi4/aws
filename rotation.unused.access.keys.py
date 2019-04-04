#!/usr/bin/env python3

import boto3
import datetime
import sys

resource = boto3.resource('iam')
client = boto3.client('iam')
today = datetime.date.today()
# Reading required inactivity threshold
thresholdDays = int(sys.stdin.read())
threshold = datetime.timedelta(days=thresholdDays)
# some trick to get keys that are never used
notAvaiableKey = 'N/A'


def deactivateAcessKey(AccessId, user):
    client.update_access_key(AccessKeyId=AccessId, Status='Inactive',
                             UserName=user.user_name)


def deleteObsoleteKey(AccessId, user):
    client.delete_access_key(AccessKeyId=AccessId,
                             UserName=user.user_name)


def createNewAccessKey(user):
    client.create_access_key(UserName=user.user_name)


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
                        deactivateAcessKey(AccessId, user)
                        deleteObsoleteKey(AccessId, user)
                        createNewAccessKey(user)
                # else check its last used date
                else:
                    lastUsedTimestamp = LastUsed['AccessKeyLastUsed'].get('LastUsedDate')
                    last = lastUsedTimestamp.date()
                    inactiveDays = today - last
                    if (inactiveDays >= threshold):
                        # Deactivating key
                        deactivateAcessKey(AccessId, user)
