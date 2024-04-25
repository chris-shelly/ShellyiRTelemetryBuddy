import urllib3
import json
import base64
from time import time
import jwt
from joserfc.jwk import RSAKey
import boto3

client = boto3.client('ssm','us-east-1')

client_id_response = client.get_parameter(
        Name='/shelly-ir-telem/client-id'
    )
client_id = client_id_response['Parameter']['Value']

keys_url_response = client.get_parameter(
        Name='/shelly-ir-telem/keys-url'
    )
keys_url = keys_url_response['Parameter']['Value']


def decode_base64_string(input_string):
    base64_bytes = input_string.encode("ascii")
    output_string_bytes = base64.b64decode(base64_bytes + b'==')
    output_string = output_string_bytes.decode("ascii")
    return output_string

def parseCookies(headers):
    parsedCookie = {}
    if headers.get('cookie'):
        jwt_cookie = headers['cookie'][0]['value'].split(';')
        for cookie_piece in jwt_cookie:
            if cookie_piece:
                parts = cookie_piece.split('=')
                parsedCookie[parts[0].strip()] = parts[1].strip()
    return parsedCookie

def lambda_handler(event, context):
    print("event",event)
    print("context",context)
    request = event['Records'][0]['cf']['request']
    headers = request['headers']
    parsedCookies = parseCookies(headers)
    if not (parsedCookies and parsedCookies['id_token']):
        print("no JWTs detected")
        return False

    raw_id_token = parsedCookies['id_token']
    print(raw_id_token)
    http = urllib3.PoolManager()
    response = http.request('GET',keys_url)
    print(response.status)
    print(response.data.decode('utf-8'))
    print(response.headers)
    keys = json.loads(response.data)["keys"]
    print(keys)

    #each JWT has a Header, Payload, and Signature, delimited by a dot
    #the header and payload are base64-encoded, decoding to the starting character {
    base64_id_token_components = raw_id_token.split(".")
    print(base64_id_token_components)
    id_token_header = json.loads(decode_base64_string(base64_id_token_components[0]))
    print("header:",id_token_header)
    id_token_payload = json.loads(decode_base64_string(base64_id_token_components[1]))
    print("payload:",id_token_payload)
    id_token_signature = base64_id_token_components[2] #note this signature is not base64 encoded, it must be decoded with RS256
    print("signature:",id_token_signature)
    #get the kid from the header
    kid = id_token_header['kid']
    #search for the kid in the public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        print('Public key not found in jwks.json')
        return False

    public_key = keys[key_index]
    rsa_key = RSAKey.import_key(public_key)
    pem = rsa_key.as_pem(private=False)
    #verify the token
    #note that if there is an aud claim on the tokem, we must provide an audience argument in our decode function call
    try:
        decoded = jwt.decode(raw_id_token,pem,algorithms=["RS256"],audience=client_id)
        print(decoded)
    except Exception as e:
        print(e)
        print("Token could not be verified")
        return False
    #since we passeed the verification, we can check claims
    claims = id_token_payload
    print(claims)
    #verify the token is not expired
    if time() > claims['exp']:
        print('Token is expired')
        return False
    #verify the Audience
    if claims['aud'] != client_id:
        print('Token was not issued for this audience')
        return False

    
    print("JWT verified successfully")
    return request
