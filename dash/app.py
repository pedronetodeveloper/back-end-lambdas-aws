import psycopg2
import os
import json
import logging

# Configuração do Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'onboarding')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = '5432'

def get_taxa_aprovacao(cur, empresa_filter=None):
    """
    Calcula a taxa de aprovação geral dos documentos
    """
    logger.info(f"Calculando taxa de aprovação. Filtro empresa: {empresa_filter}")
    
    # Base WHERE clause para filtro por empresa
    empresa_where = ""
    empresa_params = []
    
    if empresa_filter:
        empresa_where = "JOIN candidatos c ON dc.email_candidato = c.email WHERE c.empresa = %s"
        empresa_params = [empresa_filter]
    
    # Query para calcular taxa de aprovação
    query_aprovacao = f"""
        SELECT 
            COUNT(CASE WHEN dc.status = 'APROVADO' THEN 1 END) as aprovados,
            COUNT(*) as total
        FROM documentos_candidatos dc
        {empresa_where}
    """
    
    cur.execute(query_aprovacao, empresa_params)
    result = cur.fetchone()
    
    aprovados = result[0] or 0
    total = result[1] or 1
    
    # Calcular taxa de aprovação
    taxa_aprovacao = round((aprovados / total) * 100, 1) if total > 0 else 0.0
    
    logger.info(f"Taxa calculada: {aprovados}/{total} = {taxa_aprovacao}%")
    
    return {
        'taxa_aprovacao': taxa_aprovacao,
        'documentos_aprovados': aprovados,
        'total_documentos': total,
        'empresa': empresa_filter
    }

def get_contratacoes(cur, empresa_filter=None):
    """
    Conta o número de contratações (candidatos com situação 'Processo Finalizado')
    """
    logger.info(f"Calculando número de contratações. Filtro empresa: {empresa_filter}")
    
    # Base WHERE clause para filtro por empresa
    empresa_where = "WHERE c.situacao = 'Processo Finalizado'"
    empresa_params = []
    
    if empresa_filter:
        empresa_where += " AND c.empresa = %s"
        empresa_params = [empresa_filter]
    
    # Query para contar contratações
    query_contratacoes = f"""
        SELECT COUNT(*) as total_contratacoes
        FROM candidatos c
        {empresa_where}
    """
    
    cur.execute(query_contratacoes, empresa_params)
    result = cur.fetchone()
    
    total_contratacoes = result[0] or 0
    
    logger.info(f"Total de contratações encontradas: {total_contratacoes}")
    
    return {
        'contratacoes': total_contratacoes,
        'empresa': empresa_filter
    }


def get_documentos_por_tipo(cur, empresa_filter=None):
    """
    Retorna documentos agrupados por tipo com status
    """
    logger.info(f"Calculando documentos por tipo. Filtro empresa: {empresa_filter}")
    
    # Base WHERE clause para filtro por empresa
    empresa_where = ""
    empresa_params = []
    
    if empresa_filter:
        empresa_where = "JOIN candidatos c ON dc.email_candidato = c.email WHERE c.empresa = %s"
        empresa_params = [empresa_filter]
    
    # Query para documentos por tipo
    query_docs = f"""
        SELECT 
            dc.tipo_documento,
            COUNT(*) as total,
            COUNT(CASE WHEN dc.status = 'APROVADO' THEN 1 END) as aprovados,
            COUNT(CASE WHEN dc.status = 'REPROVADO' THEN 1 END) as reprovados,
            COUNT(CASE WHEN dc.status = 'PENDENTE' THEN 1 END) as pendentes
        FROM documentos_candidatos dc
        {empresa_where}
        GROUP BY dc.tipo_documento
    """
    
    cur.execute(query_docs, empresa_params)
    results = cur.fetchall()
    
    # Montar o formato solicitado
    documentos_por_tipo = {}
    
    for row in results:
        tipo = row[0].lower() if row[0] else 'desconhecido'  # cpf, rg, etc
        total = row[1] or 0
        aprovados = row[2] or 0
        reprovados = row[3] or 0
        pendentes = row[4] or 0
        
        documentos_por_tipo[tipo] = {
            'total': total,
            'aprovado': aprovados,
            'reprovado': reprovados,
            'pendente': pendentes
        }
    
    logger.info(f"Documentos por tipo processados: {documentos_por_tipo}")
    
    return documentos_por_tipo

def lambda_handler(event, context):
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    
    logger.info(f"Taxa Aprovação API - Method: {http_method}, Path: {path}")
    
    conn = None
    cur = None
    
    try:
        # Conexão com banco
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        cur = conn.cursor()
        
        # GET /observability/taxa-aprovacao - Taxa de aprovação específica
        if path == '/observability/taxa-aprovacao' and http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            empresa_filter = query_params.get('empresa')
            
            logger.info(f"Obtendo taxa de aprovação. Empresa: {empresa_filter}")
            
            taxa_data = get_taxa_aprovacao(cur, empresa_filter)
            
            return {
                'statusCode': 200,
                'body': json.dumps(taxa_data),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # GET /observability/contratacoes - Número de contratações
        elif path == '/observability/contratacoes' and http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            empresa_filter = query_params.get('empresa')
            
            logger.info(f"Obtendo número de contratações. Empresa: {empresa_filter}")
            
            contratacoes_data = get_contratacoes(cur, empresa_filter)
            
            return {
                'statusCode': 200,
                'body': json.dumps(contratacoes_data),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # GET /observability/documentos-por-tipo - Documentos agrupados por tipo
        elif path == '/observability/documentos-por-tipo' and http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            empresa_filter = query_params.get('empresa')
            
            logger.info(f"Obtendo documentos por tipo. Empresa: {empresa_filter}")
            
            docs_por_tipo = get_documentos_por_tipo(cur, empresa_filter)
            
            return {
                'statusCode': 200,
                'body': json.dumps(docs_por_tipo),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # Rota não encontrada
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Rota não encontrada'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na API taxa aprovação: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro interno do servidor', 'details': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()