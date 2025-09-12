import json
import psycopg2
import os
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import logging
import hashlib

# Configurações do banco
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LOG: Verifica se as variáveis de ambiente do e-mail foram carregadas
EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE')
SENHA_EMAIL = os.environ.get('SENHA_REMETENTE')
logger.info(f"EMAIL_REMETENTE carregado: {'Sim' if EMAIL_REMETENTE else 'Não'}")
logger.info(f"SENHA_EMAIL carregada: {'Sim' if SENHA_EMAIL else 'Não'}")
TOKEN_EXPIRACAO_HORAS = 24  # validade do token

def gerar_token():
    return str(uuid.uuid4())

def montar_link_criar_senha(token):
    # O ideal é que essa URL base também venha de uma variável de ambiente
    return f"https://sua-plataforma.com/definir-senha?token={token}"

# Função de hash SHA256
def hash_senha(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ===== FUNÇÃO DE E-MAIL ATUALIZADA COM O SLOGAN =====
def enviar_email_link_criacao(email_destino, nome_usuario, link_criar_senha):
    assunto = "Bem-vindo ao DocFlow! Crie sua senha de acesso."
    
    # --- TEMPLATE PERSONALIZADO PARA DOCFLOW ---
    cor_principal = "#BA68C8" # Cor padrão do projeto
    slogan = "Funcionalidades prontas para agilizar suas contratações" # Slogan do TCC
    
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
            .header h1 {{ margin: 0; font-size: 28px; }}
            .header p {{ margin: 10px 0 0; font-size: 16px; opacity: 0.9; }}
            .content {{ padding: 30px; color: #333333; line-height: 1.6; }}
            .content p {{ margin: 0 0 20px; }}
            .btn-container {{ text-align: center; margin: 30px 0; }}
            .btn-plataforma {{ background-color: {cor_principal}; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; transition: background-color 0.3s; }}
            .btn-plataforma:hover {{ background-color: #4A148C; }}
            .footer {{ background-color: #f4f4f4; color: #888888; text-align: center; padding: 20px; font-size: 12px; }}
            .footer a {{ color: {cor_principal}; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bem-vindo(a) ao DocFlow!</h1>
                <p>{slogan}</p>
            </div>
            <div class="content">
                <p>Olá, {nome_usuario},</p>
                <p>Seu acesso à plataforma DocFlow foi criado com sucesso. Para garantir a segurança da sua conta, o próximo passo é definir uma senha pessoal.</p>
                <p>Por favor, clique no botão abaixo para criar sua senha. Este link é válido por 24 horas.</p>
                <div class="btn-container">
                    <a href="{link_criar_senha}" class="btn-plataforma">Criar Minha Senha</a>
                </div>
                <p>Se o botão não funcionar, você também pode copiar e colar o seguinte link no seu navegador:</p>
                <p><a href="{link_criar_senha}" style="color: {cor_principal}; word-break: break-all;">{link_criar_senha}</a></p>
                <p>Atenciosamente,<br>Equipe DocFlow</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} DocFlow. Todos os direitos reservados.</p>
                <p>Se você não solicitou este e-mail, por favor, desconsidere está mensagem ou e-mail.</p>
                <p>Dúvidas ou suporte? Entre em contato: (11) 9999-9999.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Versão em texto puro atualizada com slogan
    corpo_texto = f"""
    Olá, {nome_usuario},

    Bem-vindo(a) ao DocFlow!
    {slogan}

    Seu acesso foi criado com sucesso. Para garantir a segurança da sua conta, o próximo passo é definir uma senha pessoal.

    Copie e cole o seguinte link no seu navegador para criar sua senha:
    {link_criar_senha}

    Este link é válido por 24 horas.

    Atenciosamente,
    Equipe DocFlow
    
    (c) {datetime.now().year} DocFlow.
    """
    
    logger.info(f"Iniciando tentativa de envio de e-mail para {email_destino}")

    if not EMAIL_REMETENTE or not SENHA_EMAIL:
        logger.error("ERRO CRÍTICO: As variáveis de ambiente EMAIL_REMETENTE ou SENHA_EMAIL não estão configuradas.")
        return False

    try:
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = f"DocFlow <{EMAIL_REMETENTE}>" # Melhora a apresentação do remetente
        mensagem['To'] = email_destino

        mensagem.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        mensagem.attach(MIMEText(corpo_html, 'html', 'utf-8'))

        context = ssl.create_default_context()
        
        logger.info("Conectando ao servidor SMTP SSL (smtp.gmail.com:465)...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            logger.info(f"Realizando login com o usuário {EMAIL_REMETENTE}...")
            server.login(EMAIL_REMETENTE, SENHA_EMAIL)
            
            logger.info(f"Enviando a mensagem para {email_destino}...")
            server.sendmail(EMAIL_REMETENTE, email_destino, mensagem.as_string())
        
        logger.info(f"E-mail enviado com SUCESSO para {email_destino}")
        return True
    except Exception as e:
        logger.error(f"ERRO ao tentar enviar e-mail: {e}", exc_info=True)
        return False
        
def lambda_handler(event, context):
    # LOG: Início da execução da Lambda
    logger.info(f"Execução iniciada. Path: {event.get('rawPath')}, Método: {event.get('requestContext', {}).get('http', {}).get('method', '')}")

    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')

    # CORREÇÃO: Tratamento mais robusto do corpo da requisição
    data = {}
    if 'body' in event and event['body']:
        try:
            data = json.loads(event['body'])
            logger.info(f"Corpo da requisição processado: {data}")
        except json.JSONDecodeError:
            logger.error("Erro de JSONDecodeError: Corpo da requisição inválido.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Corpo da requisição inválido'}),
                'headers': {'Content-Type': 'application/json'}
            }
    
    response = {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    try:
        # POST /usuarios - Criação de novo usuário
        if path == '/usuarios' and http_method == 'POST':
            # ... (seu código para POST continua aqui)
            nome = data.get('nome')
            email = data.get('email')
            empresa = data.get('empresa')
            role = data.get('role', 'user')

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()

            cur.execute(
                'INSERT INTO usuarios (nome, email, role,empresa) VALUES (%s, %s, %s, %s) RETURNING id',
                (nome, email, role,empresa)
            )
            usuario_id = cur.fetchone()[0]

            token = gerar_token()
            expiracao = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRACAO_HORAS)

            cur.execute(
                'INSERT INTO reset_tokens (usuario_id, token, expiracao) VALUES (%s, %s, %s)',
                (usuario_id, token, expiracao)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            # LOG: Antes de chamar a função de envio de e-mail
            logger.info(f"Dados do usuário salvos. Chamando a função para enviar e-mail para {email}...")
            link = montar_link_criar_senha(token)
            sucesso_email = enviar_email_link_criacao(email, nome, link)

            # LOG: Verifica o resultado do envio
            if sucesso_email:
                logger.info("Função de envio de e-mail retornou SUCESSO.")
            else:
                logger.error("Função de envio de e-mail retornou FALHA.")


            response = {
                'statusCode': 201,
                'body': json.dumps({'id': usuario_id, 'nome': nome, 'email': email, 'role': role, 'empresa': empresa}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # ... (Restante do seu código para GET, PUT, DELETE, etc.)
        # GET /usuarios - Listar usuários
        elif path == '/usuarios' and http_method == 'GET':
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute('SELECT id, nome, email, role,empresa FROM usuarios')
            usuarios = [{'id': row[0], 'nome': row[1], 'email': row[2], 'role': row[3], 'empresa': row[4]} for row in cur.fetchall()]
            cur.close()
            conn.close()
            response = {
                'statusCode': 200,
                'body': json.dumps(usuarios),
                'headers': {'Content-Type': 'application/json'}
            }

        # PUT /usuarios - Atualiza dados de um usuário
        elif path == '/usuarios' and http_method == 'PUT':
            id_usuario = data.get('id')
            if not id_usuario:
                return {'statusCode': 400, 'body': json.dumps({'error': "O campo 'id' é obrigatório no corpo para atualizar."})}
            nome = data.get('nome')
            email = data.get('email')

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute(
                'UPDATE usuarios SET nome=%s, email=%s WHERE id=%s',
                (nome, email, id_usuario)
            )
            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'id': id_usuario, 'nome': nome, 'email': email}),
                'headers': {'Content-Type': 'application/json'}
            }
        # DELETE /usuarios - Deleta um usuário
        elif path == '/usuarios' and http_method == 'DELETE':
            id_usuario = data.get('id')
            if not id_usuario:
                return {'statusCode': 400, 'body': json.dumps({'error': "O campo 'id' é obrigatório no corpo para deletar."})}
            
            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            
            cur.execute('DELETE FROM reset_tokens WHERE usuario_id = %s', (id_usuario,))
            cur.execute('DELETE FROM usuarios WHERE id = %s', (id_usuario,))
            
            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'message': f'Usuário com id {id_usuario} deletado com sucesso.'}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # POST /usuarios/{id}/senha - Cria/atualiza senha
        elif path.startswith('/usuarios/') and path.endswith('/senha') and http_method == 'POST':
            id_usuario = event.get('pathParameters', {}).get('id')
            token_recebido = data.get('token')
            nova_senha = data.get('senha')

            if not token_recebido or not nova_senha:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Token e senha são obrigatórios'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                                    password=DB_PASS, port=DB_PORT)
            cur = conn.cursor()
            cur.execute(
                'SELECT id, expiracao FROM reset_tokens WHERE usuario_id = %s AND token = %s',
                (id_usuario, token_recebido)
            )
            row = cur.fetchone()

            if not row:
                cur.close()
                conn.close()
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Token inválido'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            token_id, expiracao = row
            if datetime.utcnow() > expiracao:
                cur.execute('DELETE FROM reset_tokens WHERE id = %s', (token_id,))
                conn.commit()
                cur.close()
                conn.close()
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Token expirado'}),
                    'headers': {'Content-Type': 'application/json'}
                }

            senha_hash = hash_senha(nova_senha)

            cur.execute('UPDATE usuarios SET senha = %s WHERE id = %s', (senha_hash, id_usuario))
            cur.execute('DELETE FROM reset_tokens WHERE id = %s', (token_id,))

            conn.commit()
            cur.close()
            conn.close()

            response = {
                'statusCode': 200,
                'body': json.dumps({'message': 'Senha criada com sucesso'}),
                'headers': {'Content-Type': 'application/json'}
            }

    except Exception as e:
        logger.error(f"Erro no lambda: {str(e)}", exc_info=True)
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }

    return response