import json
from elasticsearch import Elasticsearch, RequestsHttpConnection
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

headers = { "Content-Type": "application/json" }
region = 'us-east-1'

es_host = 'search-photos-kirpvnx6l5zx6pqlxfipgs5rma.aos.us-east-1.on.aws' 
es = Elasticsearch(
        hosts=[{'host': es_host, 'port': 443}],
        http_auth=('es-user', 'Password@12'),  # Replace with your OpenSearch username and password
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
lex_client = boto3.client('lexv2-runtime', region_name='us-east-1')

def cleanData(query):
    word_list = query.split(" ")
    w_list=[]
    for word in word_list:
        if (word=="and" or word=="or" or word==","):
            continue
        w_list.append(word)
    return w_list

    
def get_labels(message):
    # Assuming 'message' contains the text to send to Lex
    # Replace 'BotName' and 'BotAlias' with your Lex bot's name and alias
    lex_response = lex_client.post_text(
        botName='PhotoBot',
        botAlias='	TestBotAlias',
        userId='12345',
        inputText=message
    )

    print(lex_response["message"])

    # Here you can format the Lex response as needed
    return {
        "type": "unstructured",
        "unstructured": {
            "id": "string",  # Modify as necessary
            "text": lex_response['message'],  # Using the message from Lex response
            "timestamp": "string"  # Modify as necessary
        }
    }
    

def get_photo_path(keywords):
    index_name='photos'
    query = {
        "size": 100,
        "query": {
            "multi_match": {
                "query": keywords,
            }
        }
    }
    
    response = es.search(index=index_name, body=query)
    
    photos_to_fetch = []
    
    for i in response['hits']['hits']:
        name = i['_source']['objectKey']
        bucket = i['_source']['bucket']
        photos_to_fetch.append(f'https://hw3-b2photos.s3.amazonaws.com/{name}')
        
    return photos_to_fetch 


def lambda_handler(event, context):
    query = event['queryStringParameters']['q']
    
    response = lex_client.recognize_text(
        botAliasId = 'ZUBSQAKX0T',
        botId = 'JRTLJL5846',
        localeId = 'en_US',
        sessionId = '12345',
        text=query
    )
    
    msg = ""

    if 'sessionState' in response and 'intent' in response['sessionState']:
        interpreted_intent = response['sessionState']['intent']
        
        if 'slots' in interpreted_intent:
            slots = interpreted_intent['slots']
            
            extracted_slots = {slot_name: slot_detail['value']['interpretedValue'] for slot_name, slot_detail in slots.items() if slot_detail}
            
            msg = "Extracted Slots:", extracted_slots
        else:
            msg = "No slots found in the response."
    else:
        msg = "No intent information found in the response."
        
    
    print(msg)
    labels = cleanData(extracted_slots['query'])
    
    print(labels)
    
    image_array = []
    for label in labels:
        image_array.extend(get_photo_path(label))
        
    image_array = list(set(image_array))

    
    return {
        'statusCode': 200,
        'headers':{
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({"keys":image_array})
    }
    
