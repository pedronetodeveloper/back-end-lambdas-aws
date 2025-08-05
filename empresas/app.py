import psycopg2
import os
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

def lambda_handler(event, context):
    print("EVENT RAW PATH:", event.get('rawPath'))
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    response = {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    # Tenta carregar o body como JSON
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
        data = event  # fallback

    try:
        # POST /empresas
        if path == '/empresas' and http_method == 'POST':
            nome = data.get('nome')
            cnpj = data.get('cnpj')
            planos = data.get('planos')  # Novo atributo
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('INSERT INTO empresas (nome, cnpj, planos) VALUES (%s, %s, %s) RETURNING id', (nome, cnpj, json.dumps(planos)))
            empresa_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 201,
                'body': json.dumps({'id': empresa_id, 'nome': nome, 'cnpj': cnpj, 'planos': planos}),
                'headers': {'Content-Type': 'application/json'}
            }

        # GET /empresas
        elif path == '/empresas' and http_method == 'GET':
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, nome, cnpj, planos FROM empresas')
            empresas = [{'id': row[0], 'nome': row[1], 'cnpj': row[2], 'planos': row[3]} for row in cur.fetchall()]
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps(empresas),
                'headers': {'Content-Type': 'application/json'}
            }

        # PUT /empresas/{id}
        elif path.startswith('/empresas/') and http_method == 'PUT':
            empresa_id = event.get('pathParameters', {}).get('id')
            nome = data.get('nome')
            cnpj = data.get('cnpj')
            planos = data.get('planos')
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('UPDATE empresas SET nome=%s, cnpj=%s, planos=%s WHERE id=%s', (nome, cnpj, json.dumps(planos), empresa_id))
            conn.commit()
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps({'id': empresa_id, 'nome': nome, 'cnpj': cnpj, 'planos': planos}),
                'headers': {'Content-Type': 'application/json'}
            }

        # DELETE /empresas/{id}
        elif path.startswith('/empresas/') and http_method == 'DELETE':
            empresa_id = event.get('pathParameters', {}).get('id')
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('DELETE FROM empresas WHERE id=%s', (empresa_id,))
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