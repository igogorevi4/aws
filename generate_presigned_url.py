#!/usr/bin/env python3

import boto3

# script generates pre-signed URL which you can use to upload file to AWS S3

bucket_name = 'YOURBUKETNAME'
# path to file
object_name = 'testfile'
fields = {}
# conditions = []
expiration = 3600

# Generate a presigned S3 POST URL
s3_client = boto3.client('s3')
response = s3_client.generate_presigned_post(Bucket=bucket_name,
                                             Key=object_name,
                                             Fields=fields,
                                            #  Conditions=conditions,
                                             ExpiresIn=expiration)

url = response.get('url')
access_key_id = fields['AWSAccessKeyId']
policy = fields['policy']
signature = fields['signature']
        
curl_command = 'curl -F key=' + object_name + \
               ' -F AWSAccessKeyId=' + access_key_id + \
               ' -F policy=' + policy + \
               ' -F signature=' + signature + \
               ' -F file=@' + object_name + ' ' + url

print(curl_command)