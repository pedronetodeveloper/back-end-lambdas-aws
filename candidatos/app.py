import psycopg2
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.seudominio.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', 'no-reply@seudominio.com')
EMAIL_PASS = os.environ.get('EMAIL_PASS', 'senha-email')

def gerar_senha(tamanho=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=tamanho))

def enviar_email(destinatario, usuario, senha):
    corpo = f"Olá,\n\nSeu acesso foi criado!\nUsuário: {usuario}\nSenha: {senha}\n\nAcesse a plataforma para iniciar o onboarding."
    msg = MIMEText(corpo)
    msg['Subject'] = 'Acesso à Plataforma de Onboarding'
    msg['From'] = EMAIL_USER
    msg['To'] = destinatario
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())

def lambda_handler(event, context):
    path = event.get('resource', '')
    http_method = event.get('httpMethod', '')
    response = {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    # POST /candidatos
    if path == '/candidatos' and http_method == 'POST':
        data = json.loads(event['body'])
        nome = data.get('nome')
        email = data.get('email')
        senha = gerar_senha()
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('INSERT INTO candidatos (nome, email, senha) VALUES (%s, %s, %s) RETURNING id', (nome, email, senha))
            candidato_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            enviar_email(email, email, senha)
            response = {
                'statusCode': 201,
                'body': json.dumps({'id': candidato_id, 'email': email, 'senha': senha}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # GET /candidatos
    elif path == '/candidatos' and http_method == 'GET':
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, nome, email FROM candidatos')
            candidatos = [{'id': row[0], 'nome': row[1], 'email': row[2]} for row in cur.fetchall()]
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps(candidatos),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # PUT /candidatos/{id}
    elif path == '/candidatos/{id}' and http_method == 'PUT':
        id = event['pathParameters']['id']
        data = json.loads(event['body'])
        nome = data.get('nome')
        email = data.get('email')
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('UPDATE candidatos SET nome=%s, email=%s WHERE id=%s', (nome, email, id))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'id': id, 'nome': nome, 'email': email}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # DELETE /candidatos/{id}
    elif path == '/candidatos/{id}' and http_method == 'DELETE':
        id = event['pathParameters']['id']
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('DELETE FROM candidatos WHERE id=%s', (id,))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'result': 'Candidato deletado'}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    return response
