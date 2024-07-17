
import boto3
import json


s3 = boto3.client('s3')
bucket_name = 'i-dot-ai-dev-consultations-data'
response = s3.get_object(Bucket=bucket_name, Key='test.json')
file_content = response['Body'].read().decode('utf-8')
json_content = json.loads(file_content)
print(json_content)