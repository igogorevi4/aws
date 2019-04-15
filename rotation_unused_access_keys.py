#!/usr/bin/env python3
# to test run script like that: export THRESHOLD=7 && export DAYSTOEXPIRATION="10, 5" && export ADMINEMAIL=admin@example.com && python3 rotation_unused_access_keys.py

import boto3
import datetime
import os


class RotateAccessKey:
    def __init__(self):
        self.resource = boto3.resource('iam')
        self.client = boto3.client('iam')
        self.today = datetime.date.today()
        # Reading required inactivity threshold
        threshold_days = int(os.environ['THRESHOLD'])
        self.threshold = datetime.timedelta(days=threshold_days)
        self.days_to_expiration_list = os.environ['DAYSTOEXPIRATION'].split()
        self.admin_email = str(os.environ['ADMINEMAIL'])
        self.email_sender = admin_email

    def __call__(self):
        for user in self.resource.users.all():
            self.check_user_not_service_admin(user)

    def check_user_not_service_admin(self, user):
        user_tags = self.client.list_user_tags(UserName=user.name)
        self.admin = [tags for tags in user_tags['Tags'] if tags['Key'] == 'admin' and tags['Value'] == 'service']
        if not self.admin:
            self.check_key(user)

    def check_key(self, user):
        for key in [key for key in user.access_keys.all() if key.status == "Active"]:
            existence_days = self.today - key.create_date.date()
            self.days_to_expiration = (self.threshold - existence_days).days
            access_id = key.access_key_id
            email_recipient = self.get_user_email(user)
            if existence_days > self.threshold:
                self.deactivate_access_key(access_id, user)
                self.create_email_about_expired_key(user, email_recipient)
            elif self.days_to_expiration in self.days_to_expiration_list:
                self.create_preliminary_email_content(user, email_recipient)

    def get_user_email(self, user):
        user_tags = self.client.list_user_tags(UserName=user.name)
        if user_tags:
            for tags in user_tags['Tags']:
                if tags['Key'] == 'email':
                    email = tags['Value']
                    return email
                else:
                    self.create_email_about_no_any_email_tag(user)

    def deactivate_access_key(self, access_id, user):
        self.client.update_access_key(AccessKeyId=access_id, Status='Inactive',
                                UserName=user.name)

    def notify_before_expiration(self, user, email_recipient, email_subject, email_body):
        self.send_message(email_subject, email_body, email_recipient)

    # notification to user berore AccessKey expirartion
    def create_preliminary_email_content(self, user, email_recipient):
        email_subject = "AWS AccessKey Expiration"
        email_body = "Your access key will expire in " + str(self.days_to_expiration) + " days"
        self.notify_before_expiration(user, email_recipient, email_subject, email_body)
        print(str(datetime.datetime.now()) + ": User " + user.name +
            " has just been notified that " + str(self.days_to_expiration) +
            " days left to AccessKey expiration")

    def create_email_about_no_any_email_tag(self, user):
        error_message = "There is no any email address associated with user " + user.name
        email_subject = "AWS: it needs to add a tag to user"
        email_body = error_message
        email_recipient = self.admin_email
        self.send_message(email_subject, email_body, email_recipient)
        print(str(datetime.datetime.now()) + ": " + error_message)

    def create_email_about_expired_key(self, user, email_recipient):
        email_subject = "AWS Access Key deactivated"
        email_body = "Your access key has been deactivated."
        self.send_message(email_subject, email_body, email_recipient)
        print(str(datetime.datetime.now()) + ": Access key for user " + user.name + " has been deactivated")

    def send_message(self, email_subject, email_body, email_recipient):
        ses = boto3.client('ses')
        message = ses.send_email(
            Source=self.email_sender,
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
        print(str(datetime.datetime.now()) + ": Notification has been successfully sent to email",email_recipient)

if __name__ == '__main__':
    RotateAccessKey()()

