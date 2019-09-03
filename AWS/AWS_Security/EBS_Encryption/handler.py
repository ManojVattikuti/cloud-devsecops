#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 11:01:10 2019

@author: manoj.vattikuti
"""

import json
import boto3
import logging
import time
import re
import botocore

session = boto3.session.Session()
client = session.client('ec2')
waiter_snapshot_complete = client.get_waiter('snapshot_completed')
waiter_instance_running = client.get_waiter('instance_running')
waiter_instance_stopped = client.get_waiter('instance_stopped')
waiter_instance_exists = client.get_waiter('instance_exists')
waiter_volume_available = client.get_waiter('volume_available')
waiter_volume_in_use = client.get_waiter('volume_in_use')

#Variables to change
EMAIL_FROM = 'xxxx'
email_to = 'xxxx'
AWS_EMAIL_REGION = 'us-east-1'


"""
Sends a failure Email to the team if the lambda function failed at any method.
"""
def send_failure_email(vol):
    print('Email Failure Notification started')
    client_ses = boto3.client('ses', region_name=AWS_EMAIL_REGION)
    data = 'EBS watcher failed either because Volume [%s] ' \
           'is not attached to any instance or Lambda function failed . This is in [%s] account and in region [%s].' % (vol,account,region)
    response_email = client_ses.send_email(
        Source=EMAIL_FROM,
        Destination={
            'ToAddresses': [email_to]
        },
        Message={
            'Subject': {
                'Data': 'IMP:EBS Watcher - UnEncrypted Volume Created but not attached or Lambda Failed for Volume: %s - AWS Account : %s' % (vol,account)
            },
            'Body': {
                'Text': {
                    'Data': data
                }
            }
        })
    print('Email Failure Notification Ended')
    return


"""
Sends a notification Email to the team after the job is done.
"""
def send_notification_email(vol,instanceid,device):
    print('Email Notification started')
    client_ses = boto3.client('ses', region_name=AWS_EMAIL_REGION)
    data = 'Volume [%s] attaching to Instance [%s] as [%s] device has been automatically ' \
           'detached as it is unencrypted. This is in Account [%s] and in region [%s].' % (vol, instanceid, device,account,region)
    response_email = client_ses.send_email(
        Source=EMAIL_FROM,
        Destination={
            'ToAddresses': [email_to]
        },
        Message={
            'Subject': {
                'Data': 'EBS Watcher - Detaching UnEncrypted Volume: %s - AWS Account : %s' % (vol,account)
            },
            'Body': {
                'Text': {
                    'Data': data
                }
            }
        })
    print('Email Notification Ended')
    return


"""
Detaches the volume from the instance
"""
def volume_detach(vol,device,instanceid):
    response = client.detach_volume(Force=True,VolumeId=vol)
    print (response)
    print ('Volume {} is unencrypted and attached as {} so its getting detached from instance {}' .format(vol,device,instanceid))
    send_notification_email(vol,instanceid,device)
    return

"""
Describes the image and if its an EMR cluster image it skips the detachment process.
EMR clusters was skipped because Encryption for EMR cluster Volumes is done at OS level
"""
def image_describe(imageid,vol,device,instanceid):
    response_image = client.describe_images(ImageIds=[imageid])
    print (response_image)
    image_name = response_image['Images'][0]['Name']
    print (image_name)
    #Update the code with the relevant search pattern(emr) 
    image_exception = re.search('(emr)',image_name)
    if image_exception:
        print (image_name+' matches to the whitelist, So volume attached to it is skipped')
    else:
        print (image_name+' is not whitelisted and its going through detachment process')
        volume_detach(vol,device,instanceid) 
    return 


"""
Describes the instance attached to the volume and checks the image id of the instance
"""
def instance_describe(instanceid,vol,device):
    try:
        waiter_instance_running.wait(InstanceIds=[instanceid],WaiterConfig={'Delay': 15,'MaxAttempts': 3})
    except:
        print('Instance might be in stopped state')
        waiter_instance_exists.wait(InstanceIds=[instanceid],WaiterConfig={'Delay': 15,'MaxAttempts': 3})
    finally:
        response_instance = client.describe_instances(InstanceIds=[instanceid])
        print (response_instance)
        imageid = response_instance['Reservations'][0]['Instances']
        imageid = imageid[0]['ImageId']
        print(imageid)
        volume_detach(vol,device,instanceid)
    return

"""
This function describes the volumes and checks if it is encrypted or not
"""
def volume_describe(vol):
    try:
        waiter_volume_in_use.wait(VolumeIds=[vol])
        response_volume = client.describe_volumes(VolumeIds=[vol])
        print (response_volume) 
        attachment = response_volume['Volumes'][0]['Attachments']
        instanceid = str(attachment[0]['InstanceId'])
        print (instanceid)
        encrypted = str(response_volume['Volumes'][0]['Encrypted'])
        print (encrypted)
        if encrypted == 'False':
            instance_describe(instanceid,vol,device)      
        elif encrypted == 'True':
            print('Volume %s is encrypted' %(vol))
        else:
            print('No Condition met for Volume id {}'.format(vol))
    except:
        print('Lambda Function Failed or Volume {} is not attached to any instance'.format(vol))
        send_failure_email(vol)
        return

"""
This function gets triggered when ever a create or Attach action occurs for ebs volume
"""
def lambda_handler(event, context):
    event_dumps =json.dumps(event)
    global region
    global account
    print(event)
    if 'createVolume' in event_dumps:
        volume = event['resources']
        region = event['region']
        print(region)
        account = event['account']
        print(account)
        print(volume)
        for vol in volume:
            vol = vol.split("/")[-1]       
            print (vol)
            volume_describe(vol)
    elif 'AttachVolume' in event_dumps:
        print('Cloud Trial Activity Attach Volume Event Occured')
        vol = event['detail']['responseElements']['volumeId']
        print(vol)
        region = event['region']
        print(region)
        account = event['account']
        print(account)
        volume_describe(vol)
    else:
        print('No Cloud Watch Matching Event found')  
    return
