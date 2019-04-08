#!/usr/bin/env python3

import boto3
import datetime
# import sys
import os

resource = boto3.resource('iam')
client = boto3.client('iam')
today = datetime.date.today()
# Reading required inactivity threshold
# threshold_days = int(sys.stdin.read())
# Environment variables
email_sender = str(os.environ['EMAILSENDER'])
email_recipient = str(os.environ['EMAILRECIPIENT'])
threshold_days = int(os.environ['THRESHOLD'])
threshold = datetime.timedelta(days=threshold_days)
# some trick to get keys that are never useds
not_available_key = 'N/A'


def send_message(user):
    ses = boto3.client('ses')
    email = ses.send_email(
        Source=email_sender,
        Destination={
            'ToAddresses': [
                email_recipient,
            ],
        },
        Message={
            'Subject': {
                'Data': 'AWS Access Key deactivated',
                'Charset': 'UTF-8',
            },
            'Body': {
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': 'Access key for user ' + user.user_name + ' has been deactivated.'
                },
            },
        },
    )


def deactivate_access_key(access_id, user):
    client.update_access_key(AccessKeyId=access_id, Status='Inactive',
                             UserName=user.user_name)


def delete_obsolete_key(access_id, user):
    client.delete_access_key(AccessKeyId=access_id,
                             UserName=user.user_name)


def create_new_access_key(user):
    client.create_access_key(UserName=user.user_name)


def main_logic():
    for user in resource.users.all():
        if user.name == 'test_user1' or user.name == 'kklk045':
            clean_key_for_user(user)


def clean_key_for_user(user):
    metadata = client.list_access_keys(UserName=user.user_name)
    if not metadata['AccessKeyMetadata']:
        return

    for key in user.access_keys.all():
        clean_key(user, key, metadata)


def clean_key(user, key, meta):
    access_id = key.access_key_id
    key_status = key.status
    last_used = client.get_access_key_last_used(AccessKeyId=access_id)
    if key_status != "Active":
        return

    # check if key is never used
    if not_available_key in last_used['AccessKeyLastUsed']['ServiceName']:
        deactivate_never_used_key(meta, access_id, user)
    else:
        deactivate_too_old_key(last_used, access_id, user)


def deactivate_never_used_key(meta, access_id, user):
    access_key_metadata = meta['AccessKeyMetadata'][0]
    creation_date = access_key_metadata['CreateDate'].date()
    unused_days = today - creation_date
    if unused_days > threshold:
        deactivate_access_key(access_id, user)
        send_message(user)


def deactivate_too_old_key(last_used, access_id, user):
    last_used_timestamp = last_used['AccessKeyLastUsed'].get('LastUsedDate')
    last = last_used_timestamp.date()
    uinactive_days = today - last
    if uinactive_days > threshold:
        deactivate_access_key(access_id, user)
        send_message(user)


main_logic()