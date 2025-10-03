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
    print(f"requestContext: {event.get('requestContext')}")
    print(f"rawPath: {event.get('rawPath')}")
    print(f"Headers recebidos: {event.get('headers')}")

    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    raw_path = event.get('rawPath', '')

    if raw_path == '/upload-doc-plataforma' and http_method == 'POST':
        try:
            body = event.get('body')
            is_base64 = event.get('isBase64Encoded', False)

            print(f"Body recebido: tipo={type(body)}, tamanho={len(body) if isinstance(body, str) else 'n/a'}")
            print(f"isBase64Encoded: {is_base64}")

            if not body:
                print("Body vazio!")
                return response_error(400, 'Corpo da requisição está vazio.')


            headers = event.get('headers') or {}
            filename = headers.get('filename') or headers.get('Filename')

            email = headers.get('email') or headers.get('Email')
            content_type = headers.get('content-type') or headers.get('Content-Type')

            # Força o content_type correto baseado na extensão do arquivo
            if filename:
                ext = filename.lower().split('.')[-1]
                if ext == 'pdf':
                    content_type = 'application/pdf'
                elif ext in ['png']:
                    content_type = 'image/png'
                elif ext in ['jpg', 'jpeg']:
                    content_type = 'image/jpeg'
                elif ext in ['gif']:
                    content_type = 'image/gif'
                # Adicione outros tipos conforme necessário
            file_content = None

            body_json = None
            if isinstance(body, str):
                try:
                    body_json = json.loads(body)
                    print(f"Body JSON decodificado: {body_json}")
                except json.JSONDecodeError:
                    print("Body não é um JSON válido!")
                    body_json = None

            if isinstance(body_json, dict):
                filename = filename or body_json.get('filename') or body_json.get('Filename')
                email = email or body_json.get('email') or body_json.get('Email')
                content_type = content_type or body_json.get('content_type') or body_json.get('Content_Type')
                file_content_b64 = body_json.get('file_content')
                print(f"filename extraído do JSON: {filename}")
                print(f"email extraído: {email}")
                print(f"content_type extraído: {content_type}")
                print(f"file_content_b64 presente? {'Sim' if file_content_b64 else 'Não'}")
                if file_content_b64:
                    try:
                        file_content = base64.b64decode(file_content_b64)
                        print(f"file_content decodificado: tamanho={len(file_content)} bytes")
                    except Exception as e:
                        print(f"Erro ao decodificar file_content: {e}")
                        return response_error(400, f"Erro ao decodificar file_content: {e}")

            if file_content is None:
                print("file_content não veio no JSON, tentando modo antigo...")
                if is_base64:
                    file_content = base64.b64decode(body)
                elif isinstance(body, bytes):
                    file_content = body
                else:
                    file_content = body.encode('utf-8')
                print(f"file_content modo antigo: tamanho={len(file_content) if file_content else 'n/a'} bytes")

            if not filename:
                print("filename não informado!")
                return response_error(400, 'Nome do arquivo não informado no header ou no corpo da requisição.')

            print(f"Chave do S3: {DOCUMENTS_FOLDER + filename}")

            key = DOCUMENTS_FOLDER + filename

            payload = {
                "operation": "upload",
                "key": key,
                "expiration": 3600,
                "email": email,  # Adicionado para garantir metadado na URL assinada
                "content_type": content_type  # Garante que o Content-Type da URL assinada será igual ao do PUT
            }

            print(f"Payload para API Gateway: {payload}")

            api_response = http.request(
                'POST',
                S3_API_GATEWAY_URL,
                body=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

            print(f"Resposta da API Gateway: status={api_response.status}")
            if api_response.status != 200:
                print("Erro ao obter URL assinada:", api_response.status, api_response.data.decode())
                return response_error(502, 'Falha ao obter URL assinada.')

            presigned_data = json.loads(api_response.data.decode())
            presigned_url = presigned_data.get('url')
            print(f"URL assinada recebida: {presigned_url}")


            # Define o Content-Type dinamicamente
            put_headers = {'Content-Type': content_type or 'application/octet-stream'}
            if email:
                put_headers['x-amz-meta-email'] = email
                print(f"Adicionando metadado x-amz-meta-email: {email}")
            print(f"Content-Type usado no upload: {put_headers['Content-Type']}")

            put_response = http.request(
                'PUT',
                presigned_url,
                body=file_content,
                headers=put_headers
            )

            print(f"Resposta do PUT no S3: status={put_response.status}")
            if put_response.status not in [200, 201]:
                print("Erro ao enviar arquivo para o S3:", put_response.status, put_response.data.decode())
                return response_error(502, 'Falha ao enviar o arquivo para o S3.')

            print(f"Upload realizado com sucesso! URL: {presigned_url.split('?')[0]}")
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
            query_params = event.get('queryStringParameters') or {}
            filename = query_params.get('filename')

            if not filename:
                return response_error(400, 'Nome do arquivo não informado no parâmetro filename.')

            key = DOCUMENTS_FOLDER + filename

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

    # Removido bloco duplicado e corrigida indentação dos elif

def response_error(status, message):
    return {
        'statusCode': status,
        'body': json.dumps({'error': message}),
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    }