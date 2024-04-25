import boto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal


client = boto3.client('ssm','us-east-1')
dynamodb_resource = boto3.resource('dynamodb')
stint_table_name_response = client.get_parameter(
        Name='/shelly-ir-telem/stint-table'
    )
stint_table_name = stint_table_name_response['Parameter']['Value']
stint_table = dynamodb_resource.Table(stint_table_name)

cognito = boto3.client('cognito-idp')

def parseAuth(auth_string):
    parsedCookie = {}
    jwt_cookies = auth_string.split(';')
    for cookie_piece in jwt_cookies:
      if cookie_piece:
        parts = cookie_piece.split('=')
        parsedCookie[parts[0].strip()] = parts[1].strip()
    return parsedCookie


def lambda_handler(event, context): # need the csv filename, the source bucket and the destination bucket
    """
    Get All Stint Reports
    """
    print("event:", event)
    print("context:", context)
    header = event['params']['header']
    auth_string = header['Authorization']
    parsedAuth = parseAuth(auth_string)
    access_token = parsedAuth['access_token']
    cognito_resp = cognito.get_user(AccessToken = access_token)
    print(cognito_resp)
    username = cognito_resp['Username']
    #determine who the user is so that we can get their stints from the table
    
    #query the DynamoDB users to drivers table for the drivers that user see stints for
    table_scan_response = stint_table.scan()
    print(table_scan_response)
    items = table_scan_response['Items']
    viewable_items = []
    for item in items:
        if 'Username' in item:
            if item['Username'] == username:
                viewable_items.append(item)
    print(viewable_items)
    response = {
        "statusCode": 200,
        "body": viewable_items
    }
    return response
