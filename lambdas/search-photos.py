import json
import boto3
import os
import requests
from requests.auth import HTTPBasicAuth

def push_to_lex(query):
    lex = boto3.client('lexv2-runtime', region_name='us-east-1')
    print("lex client initialized")
    response = lex.recognize_text(
        botId= os.environ['BOT_ID'],
        botAliasId= os.environ['BOT_ALIAS'],
        localeId='en_US',
        sessionId='user_lambda_search_photos',
        text=query
    )
    print("lex-response", response)
    labels = []
    print(f"Next: {response['sessionState']['intent']['slots']}")
    if response['sessionState']['intent']['slots'] == None:
        print(f"No photo collection for query {query}")
        return []

    for key,value in response['sessionState']['intent']['slots'].items():
        print (f"slot: {value}")
        if value != None:
            labels.append(value['value']['interpretedValue'])

    return labels

def search_elastic_search(labels):
    print("Inside elastic search")
    region = 'us-east-1' 
    service = 'es'
    url = os.environ['OPENSEARCH_URL']
    
    resp = []
    for label in labels:
        if (label is not None) and label != '':
            url2 = url+label
            response = requests.get(url2, auth=HTTPBasicAuth(os.environ['OPENSEARCH_USERNAME'], os.environ['OPENSEARCH_PASSWORD'])).json()
            
            resp.append(response)
    
    output = []
    for r in resp:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    output.append(f"{os.environ['S3_URL']}"+key)

    return output

def lambda_handler(event, context):
    print(event)
    q = event['queryStringParameters']['q']
    print(q)
    labels = push_to_lex(q)
    print("labels", labels)
    img_paths = []
    if len(labels):
        img_paths = search_elastic_search(labels)
    if len(img_paths) == 0:
        return{
            'statusCode':200,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps({
                "message": "Success",
                "data": img_paths
            })
        }
    else:  
        print(img_paths)
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps({
                "message": "Success",
                "data": img_paths
            })
        }