#!/bin/sh

[ 'slackweb' ] || pip install slackweb -t ./
zip -r ses-s3-lambda-slack.zip lambda_function.py slackweb
