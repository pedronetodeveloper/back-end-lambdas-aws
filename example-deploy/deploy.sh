#!/bin/bash

# Deploy script for AWS Lambda Onboarding System

echo "🚀 Iniciando deploy do sistema de onboarding..."

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI não está instalado. Instale primeiro:"
    echo "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI não está configurado. Execute: aws configure"
    exit 1
fi

echo "✅ Verificações iniciais concluídas"

# Build the application
echo "📦 Building application..."
sam build

if [ $? -ne 0 ]; then
    echo "❌ Build falhou"
    exit 1
fi

echo "✅ Build concluído"

# Deploy
echo "🚀 Deploying..."
if [ "$1" == "--guided" ]; then
    sam deploy --guided
else
    sam deploy
fi

if [ $? -eq 0 ]; then
    echo "✅ Deploy concluído com sucesso!"
    echo "📝 Verifique as URLs no output do CloudFormation"
else
    echo "❌ Deploy falhou"
    exit 1
fi
