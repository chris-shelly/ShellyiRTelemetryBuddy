import json
import boto3
import urllib3
from urllib.parse import parse_qs, urlencode

client = boto3.client('ssm','us-east-1')
token_endpoint_response = client.get_parameter(
        Name='/shelly-ir-telem/token-endpoint'
    )
token_endpoint = token_endpoint_response['Parameter']['Value']
client_secret_response = client.get_parameter(
        Name='/shelly-ir-telem/client-secret',
        WithDecryption=True
    )
client_secret = client_secret_response['Parameter']['Value']
client_id_response = client.get_parameter(
        Name ='/shelly-ir-telem/client-id'
    )
client_id = client_id_response['Parameter']['Value']



def lambda_handler(event, context):
    print("event:",event)
    request = event['Records'][0]['cf']['request']
    '''
    Sample code from AWS docs
    When a request contains a query string key-value pair but the origin server
    expects the value in a header, you can use this Lambda function to
    convert the key-value pair to a header. Here's what the function does:
        1. Parses the query string and gets the key-value pair.
        2. Adds a header to the request using the key-value pair that the function got in step 1.
    '''
    print("request before parsing querystring:",request)
    # Parse request querystring to get dictionary/json
    params = {k : v[0] for k, v in parse_qs(request['querystring']).items()}

    # Move auth param from querystring to headers
    headerName = 'Auth-Code'
    print("params",params)
    request['headers'][headerName.lower()] = [{'key': headerName, 'value': params['code']}]

    # Update request querystring
    request['querystring'] = urlencode(params)
    print("request after parsing querystring:",request)
    
    
    
    auth_code = params['code']
    grant_type = "authorization_code"
    
    scope = "aws.cognito.signin.user.admin profile email openid phone "
    my_app_url = "https://de8r7x19xapl4.cloudfront.net/parseauth"
    my_data = {
        "grant_type":grant_type,
        "client_id":client_id,
        "client_secret": client_secret,
        "code":auth_code,
        "redirect_uri":my_app_url,
        "scope":scope
        }
    #see AWS docs sample format for getting the token from the endpoint
    """
    POST https://mydomain.auth.us-east-1.amazoncognito.com/oauth2/token&
                                Content-Type='application/x-www-form-urlencoded'&
                                Authorization=Basic ZGpjOTh1M2ppZWRtaTI4M2V1OTI4OmFiY2RlZjAxMjM0NTY3ODkw
                                
                                grant_type=authorization_code&
                                client_id=1example23456789&
                                code=AUTHORIZATION_CODE&
                                redirect_uri=com.myclientapp://myclient/redirect
    """
    
    #encode the key value pairs into  the application/x-www-form-urlencoded format
    encoded_data = urlencode(my_data)
    print(encoded_data)
    
    content_type = "application/x-www-form-urlencoded"
    my_headers = {"Content-Type":content_type}
    http = urllib3.PoolManager()
    response = http.request('POST',token_endpoint,
            headers=my_headers,
            body=encoded_data)
    
    print(response.status)
    response_jwts = json.loads(response.data)
    
    print(response_jwts)
    
    
    #if getting tokens is successful (200), we redirect back to the homepage and add the tokens as cookies in the header
    if str(response.status) == '200':
        # Generate HTTP redirect response with 302 status code and Location header.
        print("retrieving tokens")
        print(response_jwts)
        id_tok = response_jwts['id_token']
        print(id_tok)
        access_tok = response_jwts['access_token']
        print(access_tok)
        refresh_tok = response_jwts['refresh_token']
        print(refresh_tok)
        
        print("redirecting to home page")
        response = {
            'status': '302',
            'statusDescription': 'Found',
            'headers': {
                'location': [{
                    'key': 'Location',
                    'value': 'https://de8r7x19xapl4.cloudfront.net'
                }]
            }
        }
        headers = response['headers']
        headers['set-cookie'] = [
            {'key': 'Set-Cookie', 'value': f'id_token={id_tok}; Secure; Path=/'},  # # HttpOnly cookie
            {'key': 'Set-Cookie', 'value': f'access_token={access_tok}; Secure; Path=/'},       # HttpOnly cookie
            {'key': 'Set-Cookie', 'value': f'refresh_token={refresh_tok}; HttpOnly; Secure; Path=/'},         # Secure cookie, sent over HTTPS only, HTTPOnly
        ]
        
        return response
    else:
        print("no tokens retrieved")
        response = {
            'status': '302',
            'statusDescription': 'Found',
            'headers': {
                'location': [{
                    'key': 'Location',
                    'value': 'https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-examples.html'
                }]
            }
        }
        headers = response['headers']
        headers['set-cookie'] = [
            {'key': 'Set-Cookie', 'value': 'cookie1=sugar; Max-Age=86400; Path=/'},  # Expires in 1 day
            {'key': 'Set-Cookie', 'value': 'cookie2=chocolatechip; HttpOnly; Path=/'},       # HttpOnly cookie
            {'key': 'Set-Cookie', 'value': 'cookie3=oatmeal; Secure; Path=/'},         # Secure cookie, sent over HTTPS only
        ]
        

        return response
