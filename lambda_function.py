#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import boto3
import json
import ConfigParser
import email

from email.parser import FeedParser
from email.header import decode_header

import slackweb


# Original: http://matetsu.hatenablog.com/entry/2015/12/10/235737

def lambda_handler(event, context):
    try:
        record = event['Records'][0]
        bucket_region = record['awsRegion']
        bucket_name = record['s3']['bucket']['name']
        mail_object_key = record['s3']['object']['key']

        s3 = boto3.client('s3', region_name=bucket_region)
        mail_object = s3.get_object(Bucket=bucket_name, Key=mail_object_key)
        mail_body = ''
        try:
            mail_body = mail_object['Body'].read().decode('utf-8')
        except:
            try:
                mail_body = mail_object['Body'].read().decode('iso-2022-jp')
            except:
                mail_body = mail_object['Body'].read()

        msg_object = email.message_from_string(mail_body)

        if msg_object.is_multipart():
            body = msg_object.get_payload()[0]
            if body.is_multipart():
                body = body.get_payload()[0]
        else:
            body = msg_object

        try:
            body = body.get_payload(decode=True).decode(body.get_content_charset())
        except:
            body = body.get_payload(decode=True).replace('\033$B', '\033$(Q').decode('iso-2022-jp-2004')

        (d_sub, sub_charset) = decode_header(msg_object['Subject'])[0]
        if sub_charset == None:
            subject = d_sub
        else:
            subject = d_sub.decode(sub_charset)

        (d_from, from_charset) = decode_header(msg_object['From'])[0]
        if from_charset == None:
            mfrom = d_from
        else:
            mfrom = d_from.decode(from_charset)
    except:
        subject = u'Error!'
        body = u"メールを受信しましたが、エラーが発生しました。"
        mfrom = u"送信元不明"

    attachments = []
    attachment = {
        'fallback': u"メール通知",
        'pretext': u"メールを受信しました\nFrom:%s " % mfrom,
        'color': '#1172B6',
        'fields': [{'title': subject, 'value': body, 'short': True}],
    }

    attachments.append(attachment)

    slack = slackweb.Slack(url=os.environ.get('SLACK_URL', ''))
    slack.notify(
        attachments=attachments,
        channel=os.environ.get('SLACK_CHANNEL', ''),
        username=os.environ.get('SLACK_USER','SES Email'),
        icon_emoji=os.environ.get('SLACK_ICON',':mailbox_with_mail:')
    )

    return 'CONTINUE'
