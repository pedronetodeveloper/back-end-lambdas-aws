import json
import psycopg2
import os
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import logging
import hashlib

# Configurações do banco
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE')
SENHA_EMAIL = os.environ.get('SENHA_EMAIL')

TOKEN_EXPIRACAO_HORAS = 24  # validade do token

def gerar_token():
    return str(uuid.uuid4())

def montar_link_criar_senha(token):
    return f"https://meusistema.com/criar-senha?token={token}"

# Função de hash SHA256
def hash_senha(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def enviar_email_link_criacao(email_destino, nome_usuario, link_criar_senha):
    assunto = "Crie sua senha no sistema"
    corpo_html = f"""
    <html>
      <body>
        <p>Olá, {nome_usuario},</p>
        <p>Seu usuário foi criado. Para finalizar o cadastro, crie sua senha clicando no link abaixo:</p>
        <p><a href="{link_criar_senha}">Criar minha senha</a></p>
        <p>Esse link é válido por 24 horas.</p>
        <p>Atenciosamente,<br>Equipe</p>
      </body>
    </html>
    """
    corpo_texto = f"""
    Olá, {nome_usuario},

    Seu usuário foi criado. Para finalizar o cadastro, acesse o link abaixo para criar sua senha:

    {link_criar_senha}

    Esse link é válido por 24 horas.

    Atenciosamente,
    Equipe
    """
    try:
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = EMAIL_REMETENTE
        mensagem['To'] = email_destino

        mensagem.attach(MIMEText(corpo_texto, 'plain'))
        mensagem.attach(MIMEText(corpo_html, 'html'))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(EMAIL_REMETENTE, SENHA_EMAIL)
            server.sendmail(EMAIL_REMETENTE, email_destino, mensagem.as_string())
        logger.info(f"Email enviado para {email_destino}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return False
def lambda_handler(event, context):
    print("EVENT RAW PATH:", event.get('rawPath'))
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')

    # Trata o corpo da requisição
    if 'body' in event and isinstance(event['body'], str):
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Corpo da requisição inválido'}),
                'headers': {'Content-Type': 'application/json'}
            }
    else:
        data = event  # útil para testes manuais no Lambda

    response = {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    try:
        # POST /usuarios - Criação de novo usuário
        if path == '/usuarios' and http_method == 'POST':
            nome = data.get('nome')
            email = data.get('email')
            role = data.get('role', 'user')

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()

            cur.execute(
                'INSERT INTO usuarios (nome, email, role) VALUES (%s, %s, %s) RETURNING id',
                (nome, email, role)
            )
            usuario_id = cur.fetchone()[0]

            token = gerar_token()
            expiracao = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRACAO_HORAS)

            cur.execute(
                'INSERT INTO reset_tokens (usuario_id, token, expiracao) VALUES (%s, %s, %s)',
                (usuario_id, token, expiracao)
            )
            conn.commit()
            cur.close()
            conn.close()

            link = montar_link_criar_senha(token)
            sucesso_email = enviar_email_link_criacao(email, nome, link)
            if not sucesso_email:
                logger.error("Erro ao enviar email para o usuário")

            response = {
                'statusCode': 201,
                'body': json.dumps({'id': usuario_id, 'nome': nome, 'email': email, 'role': role}),
                'headers': {'Content-Type': 'application/json'}
            }

        # GET /usuarios - Listar usuários
        elif path == '/usuarios' and http_method == 'GET':
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, nome, email, role FROM usuarios')
            usuarios = [{'id': row[0], 'nome': row[1], 'email': row[2], 'role': row[3]} for row in cur.fetchall()]
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps(usuarios),
                'headers': {'Content-Type': 'application/json'}
            }

        # PUT /usuarios/{id} - Atualiza dados
        elif path.startswith('/usuarios/') and http_method == 'PUT':
            id_usuario = event.get('pathParameters', {}).get('id')
            nome = data.get('nome')
            email = data.get('email')
            role = data.get('role')

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute(
                'UPDATE usuarios SET nome=%s, email=%s, role=%s WHERE id=%s',
                (nome, email, role, id_usuario)
            )
            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'id': id_usuario, 'nome': nome, 'email': email, 'role': role}),
                'headers': {'Content-Type': 'application/json'}
            }

        # POST /usuarios/{id}/senha - Cria/atualiza senha
        elif path.startswith('/usuarios/') and path.endswith('/senha') and http_method == 'POST':
            id_usuario = event.get('pathParameters', {}).get('id')
            token_recebido = data.get('token')
            nova_senha = data.get('senha')

            if not token_recebido or not nova_senha:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Token e senha são obrigatórios'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute(
                'SELECT id, expiracao FROM reset_tokens WHERE usuario_id = %s AND token = %s',
                (id_usuario, token_recebido)
            )
            row = cur.fetchone()

            if not row:
                cur.close()
                conn.close()
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Token inválido'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            token_id, expiracao = row
            if datetime.utcnow() > expiracao:
                cur.execute('DELETE FROM reset_tokens WHERE id = %s', (token_id,))
                conn.commit()
                cur.close()
                conn.close()
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Token expirado'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            senha_hash = hash_senha(nova_senha)

            cur.execute('UPDATE usuarios SET senha = %s WHERE id = %s', (senha_hash, id_usuario))
            cur.execute('DELETE FROM reset_tokens WHERE id = %s', (token_id,))

            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'message': 'Senha criada com sucesso'}),
                'headers': {'Content-Type': 'application/json'}
            }

    except Exception as e:
        logger.error(f"Erro no lambda: {str(e)}", exc_info=True)
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }

    return response