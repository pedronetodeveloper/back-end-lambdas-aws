import psycopg2
import os
import json

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

def lambda_handler(event, context):
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    
    # --- MELHORIA: Gerenciamento de conexão e cursor ---
    conn = None
    cur = None
    
    try:
        # --- CORREÇÃO: Parser de body seguro e correto ---
        data = {}
        if event.get('body'):
            try:
                # O body pode ser uma string JSON ou já um dict, este código lida com ambos
                body_content = event['body']
                data = json.loads(body_content) if isinstance(body_content, str) else body_content
            except (json.JSONDecodeError, TypeError):
                return {'statusCode': 400, 'body': json.dumps({'error': 'Corpo da requisição inválido'})}

        # --- MELHORIA: Abrir a conexão uma única vez ---
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        cur = conn.cursor()

        # --- Roteamento para /empresas ---
        if path == '/empresas':
            # POST /empresas (Criar)
            if http_method == 'POST':
                nome = data.get('nome')
                cnpj = data.get('cnpj')
                if not nome or not cnpj:
                    return {'statusCode': 400, 'body': json.dumps({'error': "Os campos 'nome' e 'cnpj' são obrigatórios."})}
                
                cur.execute(
                    'INSERT INTO empresas (nome, cnpj, telefone_responsavel, email_responsavel, planos) VALUES (%s, %s, %s, %s, %s) RETURNING id',
                    (nome, cnpj, data.get('telefone_responsavel'), data.get('email_responsavel'), data.get('planos'))
                )
                empresa_id = cur.fetchone()[0]
                conn.commit()
                response_body = {'id': empresa_id, **data}
                return {'statusCode': 201, 'body': json.dumps(response_body)}

            # GET /empresas (Listar)
            elif http_method == 'GET':
                cur.execute('SELECT id, nome, cnpj, planos, email_responsavel, telefone_responsavel FROM empresas')
                empresas = [{'id': r[0], 'nome': r[1], 'cnpj': r[2], 'planos': r[3], 'email_responsavel': r[4], 'telefone_responsavel': r[5]} for r in cur.fetchall()]
                return {'statusCode': 200, 'body': json.dumps(empresas)}

            # *** ALTERAÇÃO PRINCIPAL ***
            # PUT /empresas (Atualizar)
            elif http_method == 'PUT':
                # Pega o ID do corpo da requisição
                empresa_id = data.get('id')
                if not empresa_id:
                    return {'statusCode': 400, 'body': json.dumps({'error': "O campo 'id' é obrigatório no corpo para atualizar."})}

                nome = data.get('nome')
                cnpj = data.get('cnpj')
                if not nome or not cnpj:
                    return {'statusCode': 400, 'body': json.dumps({'error': "Os campos 'nome' e 'cnpj' são obrigatórios."})}

                cur.execute(
                    'UPDATE empresas SET nome=%s, cnpj=%s, planos=%s, email_responsavel=%s, telefone_responsavel=%s WHERE id=%s',
                    (nome, cnpj, data.get('planos'), data.get('email_responsavel'), data.get('telefone_responsavel'), empresa_id)
                )
                conn.commit()
                return {'statusCode': 200, 'body': json.dumps(data)}

            # *** ALTERAÇÃO PRINCIPAL ***
            # DELETE /empresas (Deletar)
            elif http_method == 'DELETE':
                # Pega o ID do corpo da requisição
                empresa_id = data.get('id')
                if not empresa_id:
                    return {'statusCode': 400, 'body': json.dumps({'error': "O campo 'id' é obrigatório no corpo para deletar."})}

                cur.execute('DELETE FROM empresas WHERE id=%s', (empresa_id,))
                conn.commit()
                return {'statusCode': 200, 'body': json.dumps({'message': f'Empresa com id {empresa_id} deletada.'})}
        
        # Se nenhuma rota correspondeu
        return {'statusCode': 404, 'body': json.dumps({'error': 'Rota não encontrada'})}

    except Exception as e:
        print(f"ERRO INESPERADO: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Erro interno do servidor', 'details': str(e)})}
    finally:
        # --- MELHORIA: Garante que a conexão seja sempre fechada ---
        if cur:
            cur.close()
        if conn:
            conn.close()