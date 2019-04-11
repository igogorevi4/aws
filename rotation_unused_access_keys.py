#!/usr/bin/env python3

import boto3
import datetime
import os

resource = boto3.resource('iam')
client = boto3.client('iam')
today = datetime.date.today()
# Reading required inactivity threshold
threshold_days = int(os.environ['THRESHOLD'])
threshold = datetime.timedelta(days=threshold_days)
email_sender = "eamilv@example.com"    # replace it to admin email
admin_email = "admin@example.com"


def send_message(email_subject, email_body, email_recipient):
    ses = boto3.client('ses')
    message = ses.send_email(
        Source=email_sender,
        Destination={
            'ToAddresses': [
                email_recipient,
            ],
        },
        Message={
            'Subject': {
                'Data': email_subject,
                'Charset': 'UTF-8',
            },
            'Body': {
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': email_body,
                },
            },
        },
    )
    print(str(datetime.datetime.now()) + ": Notification has been successfully sent")


# notification to user berore AccessKey expirartion
def create_preliminary_email_content(threshold, existence_days, user, email_recipient):
    days_to_expiration = (threshold - existence_days).days
    if days_to_expiration == 10 or days_to_expiration == 5:
        email_subject = "AWS AccessKey Expiration"
        email_body = "Your access key will expire in " + str(days_to_expiration) + " days"
        notify_before_expiration(user, email_recipient, email_subject, email_body)
        print(str(datetime.datetime.now()) + ": User " + user.name +
              " has just been notified that " + str(days_to_expiration) +
              " days left to AccessKey expiration")


def notify_before_expiration(user, email_recipient, email_subject, email_body):
    send_message(email_subject, email_body, email_recipient)
    print(str(datetime.datetime.now()) +
          ": User " + user.name +
          " has just been notified that 10 days left to AccessKey expiration")


def get_user_email(user):
    try:
        user_tags = client.list_user_tags(
            UserName=user.name,
        )
        for tags in user_tags['Tags']:
            if tags['Key'] == 'email':
                email = tags['Value']
                return email
    except:
        error_message = "There is no any email address associated with user " + user.name
        email_subject = "AWS: need to add tag to user"
        email_body = error_message
        email_recipient = admin_email
        send_message(email_subject, email_body, email_recipient)
        print(str(datetime.datetime.now()) + ": " + error_message)


def deactivate_access_key(access_id, user):
    client.update_access_key(AccessKeyId=access_id, Status='Inactive',
                             UserName=user.name)


def main_logic():
    for user in resource.users.all():
        deactivate_key_for_user(user)


def deactivate_key_for_user(user):
    for key in user.access_keys.all():
        access_id = key.access_key_id
        key_status = key.status
        creation_date = key.create_date.date()
        if key_status == "Active":
            expiration_key(access_id, user, creation_date)
            

def expiration_key(access_id, user, creation_date):    
    existence_days = today - creation_date
    email_recipient = get_user_email(user)
    create_preliminary_email_content(threshold, existence_days, user, email_recipient)
    if existence_days > threshold:
        deactivate_access_key(access_id, user)
        email_subject = "AWS Access Key deactivated"
        email_body = "Your access key has been deactivated."
        send_message(email_subject, email_body, email_recipient)
        print(str(datetime.datetime.now()) + ": Access key for user " + user.name + " has been deactivated")
        

main_logic()
