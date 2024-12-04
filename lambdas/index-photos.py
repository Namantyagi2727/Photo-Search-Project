import json
import boto3
import os
from datetime import *
from opensearchpy import OpenSearch, RequestsHttpConnection

ES_HOST = os.environ['ES_HOST']
REGION = os.environ['REGION']

es = OpenSearch(
    hosts = [{'host': ES_HOST, 'port': 443}],
    http_auth = (os.environ['OPENSEARCH_USERNAME'], os.environ['OPENSEARCH_PASSWORD']),
    port = 443,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

def get_url(index, type):
    url = ES_HOST + '/' + index + '/' + type
    return url

def lambda_handler(event, context):
    print(f"S3 PUT EVENT : {json.dumps(event)}")
    print('testing')
    headers = { "Content-Type": "application/json" }
    rek = boto3.client('rekognition', region_name='us-east-1')
    s3 = boto3.client('s3')
    record = event['Records'][0]
    
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    print(f'BUCKET: {bucket} ; KEY: {key}')

    # detect the labels of current image
    labels = rek.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        MaxLabels=10
    )

    metadata_response = s3.head_object(Bucket=bucket, Key=key)
    print(f'Metadata : {metadata_response}')
    custom_labels = metadata_response['Metadata'].get('customlabels', '')
    print(f'Custom Labels : {custom_labels}')
    custom_labels_list = custom_labels.split(',') if custom_labels else []

    print(f"IMAGE LABELS : {labels['Labels']}")
    
    obj = {}
    obj['objectKey'] = key
    obj["bucket"] = bucket
    obj["createdTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    obj["labels"] = []
        
    for label in labels['Labels']:
        obj["labels"].append(label['Name'])

    if len(custom_labels_list):
        obj['labels'].extend(custom_labels_list)

    print(f"JSON OBJECT : {obj}")
    
    # post the JSON object into ElasticSearch, _id is automaticlly increased
    url = get_url('photos', 'Photo')
    print(f"ES URL : {url}")

    result = es.index(index="photos", body=obj)

    print(f"Success: {result}" )
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            'Content-Type': 'application/json'
        },
        'body': json.dumps("Image labels have been successfully detected!")
    }