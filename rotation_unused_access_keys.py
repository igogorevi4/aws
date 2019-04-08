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


def deactivate_access_key(AccessId, user):
    client.update_access_key(AccessKeyId=AccessId, Status='Inactive',
                             UserName=user.user_name)


def delete_obsolete_key(AccessId, user):
    client.delete_access_key(AccessKeyId=AccessId,
                             UserName=user.user_name)


def create_new_access_key(user):
    client.create_access_key(UserName=user.user_name)


def main_logic():
    for user in resource.users.all():
        clean_key_for_user(user)


def clean_key_for_user(user):
    Metadata = client.list_access_keys(UserName=user.user_name)
    if not Metadata['AccessKeyMetadata']:
        return

    for key in user.access_keys.all():
        clean_key(user, key, Metadata)


def clean_key(user, key, meta):
    AccessId = key.access_key_id
    Status = key.status
    LastUsed = client.get_access_key_last_used(AccessKeyId=AccessId)
    if Status != "Active":
        return

    # check if key is never used
    if notAvaiableKey in LastUsed['AccessKeyLastUsed']['ServiceName']:
        deactivate_never_used_key(meta, AccessId, user)
    # else check its last used date
    else:
        deactivate_too_old_key(LastUsed, AccessId, user)


def deactivate_never_used_key(meta, AccessId, user):
    access_key_metadata = meta['AccessKeyMetadata'][0]
    creationDate = access_key_metadata['CreateDate'].date()
    unsedDays = today - creationDate
    if (unsedDays > threshold):
        # Deactivating key
        deactivate_access_key(AccessId, user)


def deactivate_too_old_key(LastUsed, AccessId, user):
    lastUsedTimestamp = LastUsed['AccessKeyLastUsed'].get('LastUsedDate')
    last = lastUsedTimestamp.date()
    inactiveDays = today - last
    if (inactiveDays > threshold):
        # Deactivating key
        deactivate_access_key(AccessId, user)


main_logic()