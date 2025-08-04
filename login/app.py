import json
import psycopg2
import os

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

def lambda_handler(event, context):
    if event.get('resource', '') == '/login' and event.get('httpMethod', '') == 'POST':
        data = json.loads(event['body'])
        username = data.get('username')
        password = data.get('password')
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, username, senha, role FROM usuarios WHERE username = %s', (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user and user[2] == password:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'token': 'fake-jwt-token',
                        'user': {
                            'id': user[0],
                            'username': user[1],
                            'role': user[3]
                        }
                    }),
                    'headers': {'Content-Type': 'application/json'}
                }
            else:
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Credenciais inválidas'}),
                    'headers': {'Content-Type': 'application/json'}
                }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not found'}),
        'headers': {'Content-Type': 'application/json'}
    }
