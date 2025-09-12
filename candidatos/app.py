import psycopg2
import os
import smtplib
from email.mime.text import MIMEText
import json
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import hashlib # --- CORREÇÃO: Importado para hashear a senha ---

# --- MELHORIA: Configuração do Logger no início ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_PORT = 587

def gerar_senha(cpf):
    cpf_numeros = ''.join(filter(str.isdigit, cpf))
    if len(cpf_numeros) != 11:
        raise ValueError("CPF inválido")
    return cpf_numeros[:3] + cpf_numeros[-2:]

# --- MELHORIA: Função para hashear a senha ---
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()
    
# ===== FUNÇÃO DE E-MAIL ATUALIZADA COM LOGS E NOME DOCFLOW =====
def enviar_email(destinatario, nome_candidato, usuario, senha):
    assunto = 'Seu Acesso à Plataforma DocFlow Foi Criado!'
    
    cor_principal = "#6A1B9A"

    corpo_html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ background-color: {cor_principal}; color: #ffffff; padding: 40px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; color: #333333; line-height: 1.6; }}
            .credentials {{ background-color: #f9f9f9; border-left: 5px solid {cor_principal}; padding: 15px; margin: 20px 0; }}
            .credentials p {{ margin: 5px 0; }}
            .btn-container {{ text-align: center; margin: 30px 0; }}
            .btn-plataforma {{ background-color: {cor_principal}; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; transition: background-color 0.3s; }}
            .btn-plataforma:hover {{ background-color: #4A148C; }}
            .footer {{ background-color: #f4f4f4; color: #888888; text-align: center; padding: 20px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bem-vindo(a) ao DocFlow!</h1>
            </div>
            <div class="content">
                <p>Olá, {nome_candidato},</p>
                <p>Seu cadastro em nossa plataforma de onboarding foi realizado com sucesso. Abaixo estão seus dados de acesso iniciais.</p>
                <div class="credentials">
                    <p><strong>Usuário:</strong> {usuario}</p>
                    <p><strong>Senha Provisória:</strong> os 3 primeiros e os 2 últimos dígitos do seu CPF.</p>
                </div>
                <div class="btn-container">
                    <a href="https://docflow.com.br/login" class="btn-plataforma">Acessar Plataforma</a>
                </div>
                <p>Recomendamos que você acesse a plataforma assim que possível para dar continuidade ao seu processo de contratação.</p>
                <p>Atenciosamente,<br>Equipe DocFlow Emai: rh@docflow.com.br</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} DocFlow. Todos os direitos reservados.</p>
                <p>Dúvidas ou suporte? Entre em contato: (11) 95813-6258 ou com o seu RH.</p>
                <p>Este é um e-mail automático. Por favor, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    corpo_texto = f"Olá, {nome_candidato},\n\nSeu cadastro na plataforma DocFlow foi realizado com sucesso.\n\nUsuário: {usuario}\nSenha Provisória: os 3 primeiros e os 2 últimos dígitos do seu CPF.\n\nAtenciosamente,\nEquipe DocFlow"

    # LOG: Ponto de partida do envio de e-mail
    logger.info(f"Iniciando tentativa de envio de e-mail para {destinatario}")

    if not EMAIL_USER or not EMAIL_PASS:
        # LOG: Erro crítico - credenciais ausentes
        logger.error("ERRO CRÍTICO: As variáveis de ambiente EMAIL_USER ou EMAIL_PASS não estão configuradas.")
        return # Adicionado 'return' para parar a execução aqui

    try:
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = f"DocFlow <{EMAIL_USER}>"
        mensagem['To'] = destinatario

        mensagem.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        mensagem.attach(MIMEText(corpo_html, 'html', 'utf-8'))
        
        # LOG: Antes da conexão com o servidor SMTP
        logger.info(f"Conectando ao servidor SMTP {EMAIL_HOST}:{EMAIL_PORT}...")
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            # LOG: Antes de fazer o login
            logger.info(f"Realizando login com o usuário {EMAIL_USER}...")
            server.login(EMAIL_USER, EMAIL_PASS)
            # LOG: Antes de enviar o e-mail
            logger.info(f"Enviando a mensagem para {destinatario}...")
            server.sendmail(EMAIL_USER, destinatario, mensagem.as_string())
        
        # LOG: Sucesso!
        logger.info(f"E-mail enviado com SUCESSO para {destinatario}.")
    except Exception as e:
        # LOG: Captura qualquer erro durante o processo
        logger.error(f"Falha ao enviar e-mail para {destinatario}: {e}", exc_info=True)

def lambda_handler(event, context):
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    
    # --- CORREÇÃO: Tratamento robusto do body ---
    data = {}
    if 'body' in event and event['body']:
        try:
            body_content = event['body']
            data = json.loads(body_content) if isinstance(body_content, str) else body_content
        except (json.JSONDecodeError, TypeError):
            return {
                'statusCode': 400, 'body': json.dumps({'error': 'Corpo da requisição inválido'}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }
    
    conn = None
    cur = None
    try:
        # --- MELHORIA: Conexão única com o banco ---
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        cur = conn.cursor()

        # POST /candidatos
        if path == '/candidatos' and http_method == 'POST':
            nome = data.get('nome')
            email = data.get('email')
            cpf = data.get('cpf')
            telefone = data.get('telefone')
            estado = data.get('estado')
            vaga = data.get('vaga')
            sexo = data.get('sexo')
            empresa = data.get('empresa')

            if not all([nome, email, cpf, empresa]):
                return {'statusCode': 400, 'body': json.dumps({'error': 'nome, email, cpf e empresa são obrigatórios'})}

            senha_plana = gerar_senha(cpf)
            # --- CORREÇÃO DE SEGURANÇA: Hasheando a senha ---
            senha_hash = hash_senha(senha_plana)

            cur.execute(
                'INSERT INTO candidatos (nome, email, cpf, senha, telefone, estado, vaga, sexo, situacao, empresa) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
                (nome, email, cpf, senha_hash, telefone, estado, vaga, sexo, 'Pendente', empresa)
            )
            candidato_id = cur.fetchone()[0]

            # --- NOVA LÓGICA ADICIONADA ---
            # 2. Insere na tabela 'usuarios' com a role 'candidato'
            logger.info(f"Criando registro correspondente na tabela 'usuarios' para o e-mail {email}")
            role_candidato = 'candidato'
            cur.execute(
                'INSERT INTO usuarios (nome, email, senha, role, empresa) VALUES (%s, %s, %s, %s, %s)',
                (nome, email, senha_hash, role_candidato, empresa)
            )
            
            conn.commit()

            enviar_email(email, nome, email, senha_plana) # O e-mail ainda envia a senha fácil de lembrar

            return {
                'statusCode': 201, 'body': json.dumps({'id': candidato_id, 'email': email}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # GET /candidatos
        elif path == '/candidatos' and http_method == 'GET':
            empresa_para_filtrar = data.get('empresa')
            
            # --- CORREÇÃO: Adicionada a coluna 'empresa' no SELECT ---
            sql_query = 'SELECT id, nome, email, situacao, estado, vaga, telefone, sexo, empresa FROM candidatos'
            params = []
            
            if empresa_para_filtrar:
                sql_query += ' WHERE empresa = %s'
                params.append(empresa_para_filtrar)

            cur.execute(sql_query, params)
            
            candidatos = [{'id': r[0], 'nome': r[1], 'email': r[2], 'situacao': r[3], 'estado': r[4], 'vaga': r[5], 'telefone': r[6], 'sexo': r[7], 'empresa': r[8]} for r in cur.fetchall()]
            
            return {
                'statusCode': 200, 'body': json.dumps(candidatos),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }
        
        # GET /documentos - Busca documentos do candidato pelo email
        elif path == '/candidatos/documentos' and http_method == 'GET':
            logger.info("Executando rota GET /candidatos/documentos.")
            
            # --- CORREÇÃO: Lendo o e-mail dos parâmetros da URL (query string) ---
            query_params = event.get('queryStringParameters') or {}
            email_candidato = query_params.get('email')
            
            # LOG: Verifica o e-mail recebido para o filtro
            logger.info(f"Tentando buscar documentos para o e-mail: '{email_candidato}'")
            # email_candidato = data.get('email')

            if not email_candidato:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': "O campo 'email' é obrigatório para buscar documentos."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            cur.execute(
                'SELECT nome_documento, tipo_documento, status FROM documentos_candidatos WHERE email_candidato = %s',
                (email_candidato,)
            )
            documentos = [
                {
                    'nome_documento': r[0],
                    'tipo_documento': r[1],
                    'status': r[2]
                }
                for r in cur.fetchall()
            ]
            return {
                'statusCode': 200,
                'body': json.dumps(documentos),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # PUT /candidatos/documentos/aprovar - Aprova documento pelo nome
        elif path == '/candidatos/documentos/aprovar' and http_method == 'PUT':
            logger.info("Executando rota PUT /candidatos/documentos/aprovar.")
            
            nome_documento = data.get('nome_documento')
            email_candidato = data.get('email_candidato')
            
            # LOG: Verifica os dados recebidos
            logger.info(f"Tentando aprovar documento '{nome_documento}' para o candidato '{email_candidato}'")

            if not nome_documento:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': "O campo 'nome_documento' é obrigatório para aprovar um documento."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            if not email_candidato:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': "O campo 'email_candidato' é obrigatório para identificar o candidato."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            # Verifica se o documento existe
            cur.execute(
                'SELECT id, status FROM documentos_candidatos WHERE nome_documento = %s AND email_candidato = %s',
                (nome_documento, email_candidato)
            )
            documento_existente = cur.fetchone()

            if not documento_existente:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f"Documento '{nome_documento}' não encontrado para o candidato '{email_candidato}'."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            documento_id, status_atual = documento_existente
            
            # LOG: Status atual do documento
            logger.info(f"Status atual do documento: '{status_atual}'")

            # Atualiza o status para 'Aprovado'
            cur.execute(
                'UPDATE documentos_candidatos SET status = %s WHERE id = %s',
                ('APROVADO', documento_id)
            )
            conn.commit()

            logger.info(f"Documento '{nome_documento}' aprovado com sucesso para o candidato '{email_candidato}'")

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f"Documento '{nome_documento}' aprovado com sucesso.",
                    'nome_documento': nome_documento,
                    'email_candidato': email_candidato,
                    'status_anterior': status_atual,
                    'status_atual': 'Aprovado',
                    'data_aprovacao': datetime.now().isoformat()
                }),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # PUT /candidatos/documentos/reprovar - Reprova documento pelo nome
        elif path == '/candidatos/documentos/reprovar' and http_method == 'PUT':
            logger.info("Executando rota PUT /candidatos/documentos/reprovar.")
            
            nome_documento = data.get('nome_documento')
            email_candidato = data.get('email_candidato')
            motivo_reprovacao = data.get('motivo_reprovacao', 'Não especificado')
            
            # LOG: Verifica os dados recebidos
            logger.info(f"Tentando reprovar documento '{nome_documento}' para o candidato '{email_candidato}' com motivo: '{motivo_reprovacao}'")

            if not nome_documento:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': "O campo 'nome_documento' é obrigatório para reprovar um documento."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            if not email_candidato:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': "O campo 'email_candidato' é obrigatório para identificar o candidato."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            # Verifica se o documento existe
            cur.execute(
                'SELECT id, status FROM documentos_candidatos WHERE nome_documento = %s AND email_candidato = %s',
                (nome_documento, email_candidato)
            )
            documento_existente = cur.fetchone()

            if not documento_existente:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f"Documento '{nome_documento}' não encontrado para o candidato '{email_candidato}'."}),
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                }

            documento_id, status_atual = documento_existente
            
            # LOG: Status atual do documento
            logger.info(f"Status atual do documento: '{status_atual}'")

            # Atualiza o status para 'Reprovado' e adiciona o motivo
            cur.execute(
                'UPDATE documentos_candidatos SET status = %s, motivo_reprovacao = %s, data_reprovacao = %s WHERE id = %s',
                ('Reprovado', motivo_reprovacao, datetime.now(), documento_id)
            )
            conn.commit()

            logger.info(f"Documento '{nome_documento}' reprovado com sucesso para o candidato '{email_candidato}'")

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f"Documento '{nome_documento}' reprovado com sucesso.",
                    'nome_documento': nome_documento,
                    'email_candidato': email_candidato,
                    'status_anterior': status_atual,
                    'status_atual': 'Reprovado',
                    'motivo_reprovacao': motivo_reprovacao,
                    'data_reprovacao': datetime.now().isoformat()
                }),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # GET /candidatos/documentos/todos - Lista todos os documentos com filtros
        elif path == '/candidatos/documentos/todos' and http_method == 'GET':
            logger.info("Executando rota GET /candidatos/documentos/todos.")
            
            query_params = event.get('queryStringParameters') or {}
            status_filtro = query_params.get('status')  # Filtro opcional por status
            empresa_filtro = query_params.get('empresa')  # Filtro opcional por empresa
            
            # LOG: Parâmetros de filtro recebidos
            logger.info(f"Filtros aplicados - Status: '{status_filtro}', Empresa: '{empresa_filtro}'")

            # Monta a query base
            sql_query = '''
                SELECT dc.nome_documento, dc.tipo_documento, dc.status, dc.email_candidato, 
                       c.nome as nome_candidato, c.empresa, dc.motivo_reprovacao,
                       dc.data_aprovacao, dc.data_reprovacao
                FROM documentos_candidatos dc
                INNER JOIN candidatos c ON dc.email_candidato = c.email
            '''
            params = []
            conditions = []

            # Adiciona filtros conforme necessário
            if status_filtro:
                conditions.append('dc.status = %s')
                params.append(status_filtro)
                
            if empresa_filtro:
                conditions.append('c.empresa = %s')
                params.append(empresa_filtro)

            # Adiciona condições WHERE se houver filtros
            if conditions:
                sql_query += ' WHERE ' + ' AND '.join(conditions)

            # Ordena por nome do candidato
            sql_query += ' ORDER BY c.nome, dc.nome_documento'

            cur.execute(sql_query, params)
            
            documentos = [
                {
                    'nome_documento': r[0],
                    'tipo_documento': r[1],
                    'status': r[2],
                    'email_candidato': r[3],
                    'nome_candidato': r[4],
                    'empresa': r[5],
                    'motivo_reprovacao': r[6],
                    'data_aprovacao': r[7].isoformat() if r[7] else None,
                    'data_reprovacao': r[8].isoformat() if r[8] else None
                }
                for r in cur.fetchall()
            ]
            
            logger.info(f"Retornando {len(documentos)} documentos.")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'documentos': documentos,
                    'total': len(documentos),
                    'filtros_aplicados': {
                        'status': status_filtro,
                        'empresa': empresa_filtro
                    }
                }),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # PUT /candidatos
        elif path == '/candidatos' and http_method == 'PUT': # --- CORREÇÃO: Rota consistente ---
            candidato_id = data.get('id')
            if not candidato_id:
                return {'statusCode': 400, 'body': json.dumps({'error': "O campo 'id' é obrigatório no corpo para atualizar."})}
            
            # ... (código para pegar outros campos do 'data')
            nome = data.get('nome')
            email = data.get('email')
            situacao = data.get('situacao')
            
            cur.execute(
                'UPDATE candidatos SET nome=%s, email=%s, situacao=%s WHERE id=%s',
                (nome, email, situacao, candidato_id)
            )
            conn.commit()

            return {
                'statusCode': 200, 'body': json.dumps({'message': 'Candidato atualizado com sucesso'}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }

        # DELETE /candidatos
        elif path == '/candidatos' and http_method == 'DELETE': # --- CORREÇÃO: Rota consistente ---
            candidato_id = data.get('id')
            if not candidato_id:
                return {'statusCode': 400, 'body': json.dumps({'error': "O campo 'id' é obrigatório no corpo para deletar."})}

            cur.execute('DELETE FROM candidatos WHERE id=%s', (candidato_id,))
            conn.commit()

            return {
                'statusCode': 200, 'body': json.dumps({'result': 'Candidato deletado'}),
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            }
        
        # Se nenhuma rota correspondeu, retorna 404
        return {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    except Exception as e:
        logger.error(f"Erro na execução da Lambda: {e}", exc_info=True)
        return {
            'statusCode': 500, 'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        }
    finally:
        # --- MELHORIA: Garante que a conexão seja sempre fechada ---
        if cur:
            cur.close()
        if conn:
            conn.close()