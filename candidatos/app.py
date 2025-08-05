import psycopg2
import os
import smtplib
from email.mime.text import MIMEText
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.seudominio.com')
EMAIL_USER = os.environ.get('EMAIL_USER', 'no-reply@seudominio.com')
EMAIL_PASS = os.environ.get('EMAIL_PASS', 'senha-email')
EMAIL_PORT = 587

def gerar_senha(cpf):
    cpf_numeros = ''.join(filter(str.isdigit, cpf))
    if len(cpf_numeros) != 11:
        raise ValueError("CPF inválido")
    return cpf_numeros[:3] + cpf_numeros[-2:]

def enviar_email(destinatario, usuario, senha):
    corpo = f"Olá,\n\nSeu acesso foi criado!\nUsuário: {usuario}\nSenha: os primeiros 3 digitos do seu CPF + os 2 ultimos\n\nAcesse a plataforma para iniciar o onboarding."
    msg = MIMEText(corpo)
    msg['Subject'] = 'Acesso à Plataforma de Onboarding'
    msg['From'] = EMAIL_USER
    msg['To'] = destinatario
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())

def lambda_handler(event, context):
    print("EVENT RAW PATH:", event.get('rawPath'))
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    response = {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    # Parse do body
    if 'body' in event and isinstance(event['body'], str):
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Corpo da requisição inválido'}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }
    else:
        data = {}

    try:
        # POST /candidatos
        if path == '/candidatos' and http_method == 'POST':
            nome = data.get('nome')
            email = data.get('email')
            cpf = data.get('cpf')

            if not nome or not email or not cpf:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'nome, email e cpf são obrigatórios'}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            senha = gerar_senha(cpf)

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO candidatos (nome, email, cpf, senha) VALUES (%s, %s, %s, %s) RETURNING id',
                (nome, email, cpf, senha)
            )
            candidato_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            enviar_email(email, email, senha)

            response = {
                'statusCode': 201,
                'body': json.dumps({'id': candidato_id, 'email': email}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # GET /candidatos (sem CPF)
        elif path == '/candidatos' and http_method == 'GET':
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, nome, email FROM candidatos')
            candidatos = [{'id': row[0], 'nome': row[1], 'email': row[2]} for row in cur.fetchall()]
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps(candidatos),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # PUT /candidatos/{id}
        elif path.startswith('/candidatos/') and http_method == 'PUT':
            candidato_id = event.get('pathParameters', {}).get('id')
            nome = data.get('nome')
            email = data.get('email')

            if not nome or not email:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'nome e email são obrigatórios para atualização'}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute(
                'UPDATE candidatos SET nome=%s, email=%s WHERE id=%s',
                (nome, email, candidato_id)
            )
            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'id': candidato_id, 'nome': nome, 'email': email}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # DELETE /candidatos/{id}
        elif path.startswith('/candidatos/') and http_method == 'DELETE':
            candidato_id = event.get('pathParameters', {}).get('id')

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('DELETE FROM candidatos WHERE id=%s', (candidato_id,))
            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'result': 'Candidato deletado'}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        }

    return response
