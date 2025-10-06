#!/usr/bin/env python3
"""
🔗 Gerador de URLs Assinadas para S3 Access Point
Projeto TCC - Sistema de Validação de Documentos

Este script gera URLs assinadas para upload/download no S3 Access Point
para usar no Insomnia ou outras ferramentas de teste.
"""

import boto3
import json
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError

# 🔧 Configurações
ACCESS_POINT_ARN = "arn:aws:s3:us-east-1:488384385831:accesspoint/docs-process-tcc"
REGION = "us-east-1"
DEFAULT_EXPIRATION = 3600  # 1 hora em segundos

def verificar_credenciais():
    """Verifica se as credenciais AWS estão configuradas"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Credenciais AWS configuradas")
        print(f"   Account: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ Credenciais AWS não encontradas!")
        print("   Execute: aws configure")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar credenciais: {str(e)}")
        return False

def gerar_url_upload(nome_arquivo, expiration=DEFAULT_EXPIRATION, email=None, content_type='application/pdf', document_type=None):
    """
    Gera URL assinada para upload de arquivo, aceitando metadados personalizados e content-type dinâmico.
    Args:
        nome_arquivo: Nome do arquivo (ex: documentos/teste.pdf)
        expiration: Tempo de expiração em segundos
        email: E-mail do remetente (opcional, será incluído como x-amz-meta-email)
        content_type: Content-Type do arquivo (ex: application/pdf, image/png)
        document_type: Tipo do documento (opcional, será incluído como x-amz-meta-document-type)
    Returns:
        URL assinada para upload ou None se erro
    """
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        params = {
            'Bucket': ACCESS_POINT_ARN,
            'Key': nome_arquivo,
            'ContentType': content_type
        }
        
        # Adicionar metadados se fornecidos
        metadata = {}
        if email:
            metadata['email'] = email
        if document_type:
            metadata['document-type'] = document_type
        
        if metadata:
            params['Metadata'] = metadata

        url = s3_client.generate_presigned_url(
            'put_object',
            Params=params,
            ExpiresIn=expiration
        )

        expira_em = datetime.now() + timedelta(seconds=expiration)

        print(f"\U0001F4E4 URL de UPLOAD gerada:")
        print(f"   Arquivo: {nome_arquivo}")
        print(f"   Expira em: {expira_em.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   URL: {url}")
        print(f"   Content-Type: {content_type}")
        if email:
            print(f"   Metadado x-amz-meta-email: {email}")
        if document_type:
            print(f"   Metadado x-amz-meta-document-type: {document_type}")
        print()

        return url

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ Erro AWS ({error_code}): {error_msg}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

def gerar_url_download(nome_arquivo, expiration=DEFAULT_EXPIRATION):
    """
    Gera URL assinada para download de arquivo
    
    Args:
        nome_arquivo: Nome do arquivo (ex: documentos/teste.pdf)
        expiration: Tempo de expiração em segundos
    
    Returns:
        URL assinada para download ou None se erro
    """
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': ACCESS_POINT_ARN,
                'Key': nome_arquivo
            },
            ExpiresIn=expiration
        )
        
        expira_em = datetime.now() + timedelta(seconds=expiration)
        
        print(f"📥 URL de DOWNLOAD gerada:")
        print(f"   Arquivo: {nome_arquivo}")
        print(f"   Expira em: {expira_em.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   URL: {url}")
        print()
        
        return url
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ Erro AWS ({error_code}): {error_msg}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

def listar_arquivos():
    """Lista arquivos no Access Point"""
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        
        response = s3_client.list_objects_v2(Bucket=ACCESS_POINT_ARN)
        
        if 'Contents' in response:
            print(f"📁 Arquivos no Access Point:")
            for obj in response['Contents']:
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"   📄 {obj['Key']} ({size_mb:.2f} MB) - {obj['LastModified']}")
        else:
            print("📁 Access Point vazio (nenhum arquivo encontrado)")
        
        print()
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ Erro ao listar arquivos ({error_code}): {error_msg}")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def gerar_collection_insomnia():
    """Gera collection do Insomnia com URLs de exemplo"""
    
    # URLs de exemplo
    upload_url = gerar_url_upload("documentos/exemplo.pdf", 7200, email="teste@exemplo.com", document_type="CV")  # 2 horas
    download_url = gerar_url_download("documentos/exemplo.pdf", 7200)
    
    if not upload_url or not download_url:
        print("❌ Não foi possível gerar URLs para o Insomnia")
        return
    
    collection = {
        "_type": "export",
        "__export_format": 4,
        "__export_date": datetime.now().isoformat(),
        "__export_source": "insomnia.desktop.app:v2023.1.0",
        "resources": [
            {
                "_id": "req_upload_s3",
                "_type": "request",
                "parentId": "fld_s3_access_point",
                "modified": int(datetime.now().timestamp() * 1000),
                "created": int(datetime.now().timestamp() * 1000),
                "url": upload_url,
                "name": "📤 Upload Documento",
                "description": "Upload de documento para S3 Access Point via URL assinada",
                "method": "PUT",
                "body": {
                    "mimeType": "application/octet-stream",
                    "fileName": "example.pdf"
                },
                "parameters": [],
                "headers": [
                    {
                        "name": "Content-Type",
                        "value": "application/pdf"
                    }
                ],
                "authentication": {},
                "metaSortKey": -1691234567000,
                "isPrivate": False
            },
            {
                "_id": "req_download_s3",
                "_type": "request",
                "parentId": "fld_s3_access_point",
                "modified": int(datetime.now().timestamp() * 1000),
                "created": int(datetime.now().timestamp() * 1000),
                "url": download_url,
                "name": "📥 Download Documento",
                "description": "Download de documento do S3 Access Point via URL assinada",
                "method": "GET",
                "body": {},
                "parameters": [],
                "headers": [],
                "authentication": {},
                "metaSortKey": -1691234566000,
                "isPrivate": False
            },
            {
                "_id": "fld_s3_access_point",
                "_type": "request_group",
                "parentId": "wrk_main",
                "modified": int(datetime.now().timestamp() * 1000),
                "created": int(datetime.now().timestamp() * 1000),
                "name": "📦 S3 Access Point - TCC",
                "description": "Requests para testar S3 Access Point do projeto TCC",
                "environment": {},
                "environmentPropertyOrder": None,
                "metaSortKey": -1691234567000
            },
            {
                "_id": "wrk_main",
                "_type": "workspace",
                "parentId": None,
                "modified": int(datetime.now().timestamp() * 1000),
                "created": int(datetime.now().timestamp() * 1000),
                "name": "TCC - Sistema Validação Documentos",
                "description": "Collection para testar o sistema de validação de documentos",
                "scope": "collection"
            }
        ]
    }
    
    # Salvar collection
    filename = f"insomnia_collection_tcc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Collection do Insomnia gerada: {filename}")
    print(f"   Para importar: Insomnia > Application > Preferences > Data > Import Data")
    print()


# --- Lambda Handler ---
def lambda_handler(event, context):
    """
    Lambda handler para gerar URL assinada de upload/download no S3 Access Point.
    Espera no event:
      {
        "operation": "upload" ou "download",
        "key": "documentos/teste.pdf",
        "expiration": 3600 (opcional),
        "email": "usuario@email.com" (opcional),
        "content_type": "application/pdf" (opcional),
        "document_type": "CV" (opcional)
      }
    """

    print("EVENTO RECEBIDO:", json.dumps(event))
    # Se vier via API Gateway, os dados estão em event['body'] (string JSON)
    if 'body' in event:
        try:
            event = json.loads(event['body'])
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Body inválido: {str(e)}"})
            }
    operation = event.get("operation")
    key = event.get("key")
    expiration = event.get("expiration", DEFAULT_EXPIRATION)
    email = event.get("email")
    content_type = event.get("content_type", "application/pdf")
    document_type = event.get("document_type")

    if not operation or not key:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Parâmetros obrigatórios: operation (upload|download) e key"
            })
        }

    if operation == "upload":
        url = gerar_url_upload(key, expiration, email=email, content_type=content_type, document_type=document_type)
        if url:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "url": url,
                    "operation": "upload",
                    "key": key,
                    "expiration": expiration,
                    "email": email,
                    "document_type": document_type
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Erro ao gerar URL de upload"})
            }
    elif operation == "download":
        url = gerar_url_download(key, expiration)
        if url:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "url": url,
                    "operation": "download",
                    "key": key,
                    "expiration": expiration
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Erro ao gerar URL de download"})
            }
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "operation deve ser 'upload' ou 'download'"})
        }
