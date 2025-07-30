import boto3
import os
import json
import base64

S3_BUCKET = os.environ.get('S3_BUCKET', 'nome-do-seu-bucket')
S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
s3 = boto3.client('s3', region_name=S3_REGION)

def lambda_handler(event, context):
    if event.get('resource', '') == '/upload-documento' and event.get('httpMethod', '') == 'POST':
        try:
            body = event['body']
            is_base64 = event.get('isBase64Encoded', False)
            if is_base64:
                file_content = base64.b64decode(body)
            else:
                file_content = body.encode()

            # O nome do arquivo deve ser enviado em um header ou no body (exemplo: header 'filename')
            filename = event['headers'].get('filename')
            if not filename:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Nome do arquivo não informado'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=file_content)
            url = f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}'
            return {
                'statusCode': 200,
                'body': json.dumps({'url': url}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not found'}),
        'headers': {'Content-Type': 'application/json'}
    }
