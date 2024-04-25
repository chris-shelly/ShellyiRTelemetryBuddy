import json
import boto3

s3_client = boto3.client('s3', region_name = 'us-east-1')
dynamodb_resource = boto3.resource('dynamodb')

client = boto3.client('ssm','us-east-1')
bucket_name_response = client.get_parameter(
        Name='/shelly-ir-telem/telem-input-bucket'
    )
bucket_name = bucket_name_response['Parameter']['Value']

cognito = boto3.client('cognito-idp')

def parseAuth(auth_string):
    """
    Function to parse the Authorization header to get the access token out of the cookie
    """
    parsedCookie = {}
    jwt_cookies = auth_string.split(';')
    for cookie_piece in jwt_cookies:
      if cookie_piece:
        parts = cookie_piece.split('=')
        parsedCookie[parts[0].strip()] = parts[1].strip()
    return parsedCookie


def lambda_handler(event, context):
    """
    Generate a presigned Amazon S3 URL that can be used to perform an action
    """
    print("event:",event)
    print("context:",context)
    object_name = event['body-json']['fileName']
    header = event['params']['header']
    auth_string = header['Authorization']
    parsedAuth = parseAuth(auth_string)
    access_token = parsedAuth['access_token']
    cognito_resp = cognito.get_user(AccessToken = access_token)
    print(cognito_resp)
    username = cognito_resp['Username']
    #determine who the user is
    
    object_name = object_name.replace(".csv",f"--{username}--.csv")
    #append the username to the name of the file so that its there when the user uploads it
    expires_in = 3600 #URL expiry time in seconds
    try:
        url = s3_client.generate_presigned_url('put_object',
                                               Params={'Bucket': bucket_name,
                                                       'Key': object_name,
                                                       'ContentType':'text/csv'},
                                                       ExpiresIn = expires_in
        )
        print("Pre-signed URL:", url)
        #send the URL back to the client
    except NoCredentialsError:
        print("Credentials not available")

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin':'*', 
            'Access-Control-Allow-Credentials': True,  # Required for cookies, authorization headers with HTTPS 
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
        }, 
        'body': url
        
    }
