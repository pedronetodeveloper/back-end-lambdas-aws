import json
import psycopg2
import os
import hashlib

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

def hash_password(password: str) -> str:
    # Hash SHA256 simples
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    print("EVENT RAW PATH:", event.get('rawPath'))
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    print("HTTP METHOD:", http_method)

    # Tratamento do corpo da requisição (JSON string ou dict)
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
        data = event  # Caso já seja dict, por exemplo no teste direto do Lambda

    # Verifica se é POST para /login
    if event.get('rawPath', '') == '/login' and http_method == 'POST':
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email e senha são obrigatórios'}),
                'headers': {'Content-Type': 'application/json'}
            }

        try:
            conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, email, senha, role FROM usuarios WHERE email = %s', (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                id_, email_db, senha_hash_db, role_db = user
                senha_calculada = hash_password(password)
                print(f"Senha calculada: {senha_calculada}")
                print(f"Senha no banco: {senha_hash_db}")

                if senha_calculada == senha_hash_db:
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'token': 'jwt-token',
                            'user': {
                                'id': id_,
                                'email': email_db,
                                'role': role_db
                            }
                        }),
                        'headers': {'Content-Type': 'application/json'}
                    }

            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Credenciais inválidas'}),
                'headers': {'Content-Type': 'application/json'}
            }

        except Exception as e:
            print(f"Erro na conexão ou consulta: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    # Caso o caminho ou método não seja esperado:
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not found'}),
        'headers': {'Content-Type': 'application/json'}
    }
