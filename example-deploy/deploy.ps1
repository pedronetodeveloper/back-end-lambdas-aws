# Deploy script for AWS Lambda Onboarding System (PowerShell)

Write-Host "🚀 Iniciando deploy do sistema de onboarding..." -ForegroundColor Green

# Check if SAM CLI is installed
try {
    sam --version | Out-Null
    Write-Host "✅ SAM CLI encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ SAM CLI não está instalado. Instale primeiro:" -ForegroundColor Red
    Write-Host "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" -ForegroundColor Yellow
    exit 1
}

# Check if AWS CLI is configured
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS CLI configurado" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI não está configurado. Execute: aws configure" -ForegroundColor Red
    exit 1
}

# Build the application
Write-Host "📦 Building application..." -ForegroundColor Blue
sam build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build falhou" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build concluído" -ForegroundColor Green

# Deploy
Write-Host "🚀 Deploying..." -ForegroundColor Blue
if ($args[0] -eq "--guided") {
    sam deploy --guided
} else {
    sam deploy
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green
    Write-Host "📝 Verifique as URLs no output do CloudFormation" -ForegroundColor Yellow
} else {
    Write-Host "❌ Deploy falhou" -ForegroundColor Red
    exit 1
}
