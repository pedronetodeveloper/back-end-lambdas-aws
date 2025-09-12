import boto3
import os
import json
import base64
import urllib3

S3_API_GATEWAY_URL = os.environ.get('S3_API_GATEWAY_URL', 'https://ktvl2lg1fh.execute-api.us-east-1.amazonaws.com/generation-uri')
DOCUMENTS_FOLDER = 'documentos/'
http = urllib3.PoolManager()
def lambda_handler(event, context):
    print('Entrou na função Lambda')
    print("Evento recebido:", json.dumps(event))

    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    raw_path = event.get('rawPath', '')

    if raw_path == '/upload-doc-plataforma' and http_method == 'POST':
        try:
            body = event.get('body')
            is_base64 = event.get('isBase64Encoded', False)

            print("Headers:", event.get('headers'))
            print("Is base64?", is_base64)
            print("Tipo do body:", type(body))

            if not body:
                return response_error(400, 'Corpo da requisição está vazio.')

            # Decodifica o conteúdo do arquivo
            if is_base64:
                file_content = base64.b64decode(body)
            else:
                if isinstance(body, bytes):
                    file_content = body
                else:
                    file_content = body.encode('utf-8')

            # Pega o nome do arquivo no header 'filename'
            headers = event.get('headers') or {}
            filename = headers.get('filename') or headers.get('Filename')

            if not filename:
                body_json = None
                if isinstance(body, str):
                    try:
                        body_json = json.loads(body)
                    except json.JSONDecodeError:
                        body_json = None
                
                if isinstance(body_json, dict):
                    filename = body_json.get('filename') or body_json.get('Filename')

            if not filename:
                return response_error(400, 'Nome do arquivo não informado no header ou no corpo da requisição.')

            key = DOCUMENTS_FOLDER + filename

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
                print("Erro ao obter URL assinada:", api_response.status, api_response.data.decode())
                return response_error(502, 'Falha ao obter URL assinada.')

            presigned_data = json.loads(api_response.data.decode())
            presigned_url = presigned_data.get('url')

            # Upload do arquivo via PUT usando a URL assinada
            put_response = http.request(
                'PUT',
                presigned_url,
                body=file_content,
                headers={'Content-Type': 'application/pdf'}
            )

            if put_response.status not in [200, 201]:
                print("Erro ao enviar arquivo para o S3:", put_response.status, put_response.data.decode())
                return response_error(502, 'Falha ao enviar o arquivo para o S3.')

            return {
                'statusCode': 200,
                'body': json.dumps({'url': presigned_url.split('?')[0]}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        except Exception as e:
            print("Erro na função:", str(e))
            return response_error(500, str(e))

    elif raw_path == '/download-doc-plataforma' and http_method == 'GET':
        try:
            # Pega o nome do arquivo dos query parameters
            query_params = event.get('queryStringParameters') or {}
            filename = query_params.get('filename')
            
            if not filename:
                return response_error(400, 'Nome do arquivo não informado no parâmetro filename.')

            key = DOCUMENTS_FOLDER + filename

            # Solicita URL assinada para download (GET)
            payload = {
                "operation": "download",
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
                print("Erro ao obter URL assinada para download:", api_response.status, api_response.data.decode())
                return response_error(502, 'Falha ao obter URL assinada para download.')

            presigned_data = json.loads(api_response.data.decode())
            presigned_url = presigned_data.get('url')

            if not presigned_url:
                return response_error(502, 'URL assinada não retornada pelo serviço.')

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'download_url': presigned_url,
                    'filename': filename,
                    'expires_in': 3600
                }),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        except Exception as e:
            print("Erro na função de download:", str(e))
            return response_error(500, str(e))

    elif http_method == 'OPTIONS':
        # Suporte para CORS preflight
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, filename, Filename'
            }
        }

    return response_error(404, 'Not found')

def response_error(status, message):
    return {
        'statusCode': status,
        'body': json.dumps({'error': message}),
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    }