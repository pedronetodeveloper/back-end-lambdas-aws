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
                <p>Recomendamos que você acesse a plataforma assim que possível para dar continuidade ao seu processo de contratação.</p>
                <p>Atenciosamente,<br>Equipe DocFlow</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} DocFlow. Todos os direitos reservados.</p>
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