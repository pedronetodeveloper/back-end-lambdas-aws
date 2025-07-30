import psycopg2
import os
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

def lambda_handler(event, context):
    path = event.get('resource', '')
    http_method = event.get('httpMethod', '')
    response = {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    # POST /usuarios
    if path == '/usuarios' and http_method == 'POST':
        data = json.loads(event['body'])
        nome = data.get('nome')
        email = data.get('email')
        role = data.get('role')
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('INSERT INTO usuarios (nome, email, role) VALUES (%s, %s, %s) RETURNING id', (nome, email, role))
            usuario_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 201,
                'body': json.dumps({'id': usuario_id, 'nome': nome, 'email': email, 'role': role}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # GET /usuarios
    elif path == '/usuarios' and http_method == 'GET':
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
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
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # PUT /usuarios/{id}
    elif path == '/usuarios/{id}' and http_method == 'PUT':
        id = event['pathParameters']['id']
        data = json.loads(event['body'])
        nome = data.get('nome')
        email = data.get('email')
        role = data.get('role')
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('UPDATE usuarios SET nome=%s, email=%s, role=%s WHERE id=%s', (nome, email, role, id))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'id': id, 'nome': nome, 'email': email, 'role': role}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # DELETE /usuarios/{id}
    elif path == '/usuarios/{id}' and http_method == 'DELETE':
        id = event['pathParameters']['id']
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('DELETE FROM usuarios WHERE id=%s', (id,))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'result': 'Usuário deletado'}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    return response
