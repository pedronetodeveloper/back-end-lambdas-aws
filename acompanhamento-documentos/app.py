import psycopg2
import os
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

def lambda_handler(event, context):
    # Espera-se que o API Gateway envie o candidato_id como pathParameter
    candidato_id = event['pathParameters']['candidato_id']
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, status, data_upload, url FROM documentos WHERE candidato_id = %s",
            (candidato_id,)
        )
        documentos = [
            {
                'id': row[0],
                'nome': row[1],
                'status': row[2],
                'data_upload': row[3],
                'url': row[4]
            } for row in cur.fetchall()
        ]
        cur.close()
        conn.close()
        return {
            'statusCode': 200,
            'body': json.dumps(documentos),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
