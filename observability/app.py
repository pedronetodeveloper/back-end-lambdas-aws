import psycopg2
import os
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

def lambda_handler(event, context):
    if event.get('resource', '') == '/observability/acuracia-por-label' and event.get('httpMethod', '') == 'GET':
        try:
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('''
                SELECT label, COUNT(*) as total, AVG(acuracia) as acuracia_media
                FROM documentos
                GROUP BY label
            ''')
            result = [
                {
                    'label': row[0],
                    'total': row[1],
                    'acuracia_media': float(row[2]) if row[2] is not None else None
                } for row in cur.fetchall()
            ]
            cur.close()
            conn.close()
            return {
                'statusCode': 200,
                'body': json.dumps(result),
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
