import json
from datetime import datetime
import boto3
import base64
from elasticsearch import Elasticsearch, RequestsHttpConnection


s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')
es_host = 'search-photos-kirpvnx6l5zx6pqlxfipgs5rma.aos.us-east-1.on.aws' 
es = Elasticsearch(
        hosts=[{'host': es_host, 'port': 443}],
        http_auth=('es-user', 'Password@12'),  # Replace with your OpenSearch username and password
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )


def lambda_handler(event, context):
    print("------------------ PHOTO UPLOADED ----------------- LF1 INVOKED -----------------")
    record = event['Records'][0]
    bucket_name = record['s3']['bucket']['name']
    object_key = record['s3']['object']['key']
    
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    base64_encoded_image_content = response['Body'].read()
    decoded_image_content = base64.b64decode(base64_encoded_image_content)
    
    rekognition_response = rekognition_client.detect_labels(
        Image={'Bytes': decoded_image_content},
        MaxLabels=15,  # Maximum labels
        MinConfidence=75  # Minimum confidence for labels
    )
    
    labels = [label['Name'] for label in rekognition_response['Labels']]
    print(labels)

    response = s3_client.head_object(Bucket=bucket_name, Key=object_key)

    # print(response.get('Metadata', {}))
    
    custom_labels = response.get('Metadata', {}).get('customlabels')
    if custom_labels:
        cl = custom_labels.split(',')
        labels.extend(cl) 
        

    document = {
        'objectKey': object_key,
        'bucket': bucket_name,
        'createdTimestamp': datetime.now().isoformat(), # Or use the S3 object's timestamp
        'labels': labels
    }
    
    # print(document)
    
    res = es.index(index="photos", body=document)
    # print(res)
    # print(res['result'])
    
    return {
        'statusCode': 200,
        'body': json.dumps(document)
    }
