import boto3
import sys
from dateutil import parser
import argparse
import os
import json

# owner ID
owner = '1234567890' 


def get_ami_list(filters):
    ec2 = boto3.client('ec2')
    images = ec2.describe_images(Owners=[owner], Filters = filters)
    list_of_images = images['Images']
    return (list_of_images)


def get_suitable_image_id(ami_list):
    image_id_list = []
    for image in ami_list:
        # if image['State'] == 'available':
        image_id = image['ImageId']
        image_id_list.append(image_id)
    # print (image_id_list)
    return image_id_list


def get_newest_image_id(ami_list):
    latest = None
    image_id = ''
    for image in ami_list:
        if image['State'] == 'available':
            if not latest:
                latest = image
                continue
            if parser.parse(image['CreationDate']) > parser.parse(latest['CreationDate']):
                latest = image
            image_id = latest['ImageId']
    latest_image_id = [image_id]
    return latest_image_id

# if __name__ == '__main__':
def lambda_handler(event, context):
    # Default values
    image_name = '*'
    image_tag = ''
    latest = False
    args = []
    arg = ''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-n', help='AMI name')
    argparser.add_argument('-t', help='AMI tag', action='append')
    argparser.add_argument('-l', help='return latest AMI', action='store_true')

    parameters = argparser.parse_args()

    if parameters.n:
        image_name = parameters.n
    if parameters.t:
        image_tag = parameters.t
    if parameters.l:
        # If THERE IS a flag just pass it to boolean
        latest = True

    if image_tag is not '':
        # Default filters
        filters = [ {
            'Name': 'name',
            'Values': [image_name]
        },{
            'Name': 'tag-key',
            'Values': image_tag
        } ]
    else:
        filters = [ {
            'Name': 'name',
            'Values': [image_name]
        }]

    ami_list = get_ami_list(filters)
    if latest:
        result = (get_newest_image_id(ami_list))
        print (result)
        return(result)
    else:
        result = (get_suitable_image_id(ami_list))
        print (result)
        return(result)

#Definitions for local testing purposes
#python-lambda-local may be useful
# context = ''
# event = {"-n": "Linux*", "-t":"*", "-l": ""}
# result = lambda_handler(event, context)
# print (result) 
