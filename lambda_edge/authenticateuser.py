import json
import boto3

cognito = boto3.client('cognito-idp', 'us-east-1')

def parseCookies(headers):
    parsedCookie = {}
    if headers.get('cookie'):
        jwt_cookies = headers['cookie'][0]['value'].split(';')
        for cookie_piece in jwt_cookies:
            if cookie_piece:
                parts = cookie_piece.split('=')
                parsedCookie[parts[0].strip()] = parts[1].strip()
    return parsedCookie


def lambda_handler(event, context):
    print("event:",event)
    request = event['Records'][0]['cf']['request']
    headers = request['headers']
    
    parsedCookies = parseCookies(headers)
    
    if parsedCookies and parsedCookies['access_token']:
        print("found cookie")
        access_token = parsedCookies['access_token']
        print(access_token)
        try:
            cognito_resp = cognito.get_user(AccessToken = access_token)
            print(request)
            return request
        except Exception as err:
            print("an Exception occured",err)
        
    
    
    response = {
        'status': '302',
        'statusDescription': 'Found',
        'headers': {
            'location': [{
                'key': 'Location',
                'value': 'https://shelly-ir-telem1.auth.us-east-1.amazoncognito.com/oauth2/authorize?client_id=6miag6a878is33ui39frqps63d&response_type=code&scope=aws.cognito.signin.user.admin+email+openid+phone+profile&redirect_uri=https%3A%2F%2Fde8r7x19xapl4.cloudfront.net%2Fparseauth',
            }],

        },
    };
    print(response)
    return response
