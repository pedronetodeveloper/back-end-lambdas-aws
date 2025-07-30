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

    # POST /empresas
    if path == '/empresas' and http_method == 'POST':
        data = json.loads(event['body'])
        nome = data.get('nome')
        cnpj = data.get('cnpj')
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('INSERT INTO empresas (nome, cnpj) VALUES (%s, %s) RETURNING id', (nome, cnpj))
            empresa_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 201,
                'body': json.dumps({'id': empresa_id, 'nome': nome, 'cnpj': cnpj}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # GET /empresas
    elif path == '/empresas' and http_method == 'GET':
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, nome, cnpj FROM empresas')
            empresas = [{'id': row[0], 'nome': row[1], 'cnpj': row[2]} for row in cur.fetchall()]
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps(empresas),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # PUT /empresas/{id}
    elif path == '/empresas/{id}' and http_method == 'PUT':
        id = event['pathParameters']['id']
        data = json.loads(event['body'])
        nome = data.get('nome')
        cnpj = data.get('cnpj')
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('UPDATE empresas SET nome=%s, cnpj=%s WHERE id=%s', (nome, cnpj, id))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'id': id, 'nome': nome, 'cnpj': cnpj}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # DELETE /empresas/{id}
    elif path == '/empresas/{id}' and http_method == 'DELETE':
        id = event['pathParameters']['id']
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('DELETE FROM empresas WHERE id=%s', (id,))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'result': 'Empresa deletada'}),
                'headers': {'Content-Type': 'application/json'}
            }
        except Exception as e:
            response = {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    return response
