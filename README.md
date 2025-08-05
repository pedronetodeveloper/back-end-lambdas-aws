# Sistema de Onboarding - Backend AWS Lambda

Este projeto implementa um sistema de onboarding usando AWS Lambda Functions, API Gateway e S3.

## Estrutura do Projeto

```
├── empresas/           # CRUD de empresas
├── usuarios/           # CRUD de usuários  
├── candidatos/         # CRUD de candidatos
├── login/              # Autenticação
├── upload-documentos/  # Upload para S3
├── acompanhamento-documentos/ # Listagem de documentos
├── observability/      # Métricas e observabilidade
├── template.yaml       # Template SAM
└── requirements.txt    # Dependências Python
```

## Pré-requisitos

1. AWS CLI configurado
2. SAM CLI instalado
3. PostgreSQL (RDS ou local)
4. Python 3.9+

## Deploy

### 1. Instalar SAM CLI
```bash
# Windows (via Chocolatey)
choco install aws-sam-cli

# Ou baixar do site oficial da AWS
```

### 2. Build e Deploy
```bash
# Build
sam build

# Deploy interativo (primeira vez)
sam deploy --guided

# Deploy subsequentes
sam deploy
```

### 3. Configurar Variáveis de Ambiente
Durante o `sam deploy --guided`, configure:
- DBHost: endpoint do RDS PostgreSQL
- DBName: nome do banco
- DBUser: usuário do banco
- DBPass: senha do banco
- DBPort: porta (padrão 5432)

## Estrutura das APIs

### Empresas
- `POST /empresas` - Criar empresa
- `GET /empresas` - Listar empresas
- `PUT /empresas/{id}` - Atualizar empresa
- `DELETE /empresas/{id}` - Deletar empresa

### Usuários
- `POST /usuarios` - Criar usuário
- `GET /usuarios` - Listar usuários
- `PUT /usuarios/{id}` - Atualizar usuário
- `DELETE /usuarios/{id}` - Deletar usuário

### Candidatos
- `POST /candidatos` - Criar candidato
- `GET /candidatos` - Listar candidatos
- `PUT /candidatos/{id}` - Atualizar candidato
- `DELETE /candidatos/{id}` - Deletar candidato

### Outros
- `POST /login` - Autenticação
- `POST /upload-documento` - Upload de arquivo
- `GET /acompanhamento-documentos/{candidato_id}` - Documentos do candidato
- `GET /observability/acuracia-por-label` - Métricas

## Banco de Dados

### Tabelas necessárias:
```sql
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) UNIQUE NOT NULL
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    senha VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user'
);

CREATE TABLE candidatos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    cpf VARCHAR(18) UNIQUE NOT NULL,
    senha VARCHAR(255)
);

CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    candidato_id INTEGER REFERENCES candidatos(id),
    nome VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url TEXT,
    label VARCHAR(100),
    acuracia DECIMAL(5,2)
);
```

## Teste Local

```bash
# Iniciar API local
sam local start-api

# Testar endpoint
curl http://localhost:3000/empresas
```

## Monitoramento

- Logs: CloudWatch Logs
- Métricas: CloudWatch Metrics
- Tracing: X-Ray (adicionar se necessário)

## Segurança

- Variáveis de ambiente para credenciais
- IAM roles com permissões mínimas
- CORS configurado no API Gateway
- S3 com acesso restrito
