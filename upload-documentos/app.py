import boto3
import os
import json
import base64
import urllib3

S3_API_GATEWAY_URL = os.environ.get('S3_API_GATEWAY_URL', 'https://ktvl2lg1fh.execute-api.us-east-1.amazonaws.com/generation-uri')
DOCUMENTS_FOLDER = 'documentos/'
http = urllib3.PoolManager()

def lambda_handler(event, context):
    if event.get('resource') == '/upload-doc-plataforma' and event.get('httpMethod') == 'POST':
        try:
            # Validação do body e base64
            body = event.get('body')
            is_base64 = event.get('isBase64Encoded', False)
            if not body:
                return response_error(400, 'Corpo da requisição está vazio.')

            file_content = base64.b64decode(body) if is_base64 else body.encode()

            filename = event['headers'].get('filename')
            if not filename:
                return response_error(400, 'Nome do arquivo não informado.')

            key = DOCUMENTS_FOLDER + filename

            # Requisição à API Gateway que gera a URL assinada
            payload = {
                "operation": "upload",
                "key": key,
                "expiration": 3600
            }

            api_response = http.request(
                'POST',
                S3_API_GATEWAY_URL,
                body=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

            if api_response.status != 200:
                return response_error(502, 'Falha ao obter URL assinada.')

            presigned_data = json.loads(api_response.data.decode())
            presigned_url = presigned_data.get('url')

            # Upload do arquivo via PUT direto na URL assinada
            put_response = http.request(
                'PUT',
                presigned_url,
                body=file_content,
                headers={'Content-Type': 'application/pdf'}
            )

            if put_response.status not in [200, 201]:
                return response_error(502, 'Falha ao enviar o arquivo para o S3.')

            return {
                'statusCode': 200,
                'body': json.dumps({'url': presigned_url.split('?')[0]}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        except Exception as e:
            return response_error(500, str(e))

    return response_error(404, 'Not found')


def response_error(status, message):
    return {
        'statusCode': status,
        'body': json.dumps({'error': message}),
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    }
