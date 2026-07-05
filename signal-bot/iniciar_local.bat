@echo off
title WDO VIP Backend
color 0A

echo.
echo  ========================================
echo   WDO VIP Backend - Iniciando...
echo  ========================================
echo.

:: Variaveis de ambiente
set DATABASE_URL=postgresql+asyncpg://postgres:postgres123@localhost:5432/wdo_vip
set DATABASE_URL_SYNC=postgresql://postgres:postgres123@localhost:5432/wdo_vip
set TELEGRAM_BOT_TOKEN=8992965841:AAGOg60JQ5ysTi9nyNcnm-B8COFuuhlJScM
set TELEGRAM_ADMIN_IDS=1191003457
set TELEGRAM_BOT_USERNAME=Wdotrader_bot
set VIP_BOT_TOKEN=8992965841:AAGOg60JQ5ysTi9nyNcnm-B8COFuuhlJScM
set VIP_CHANNEL_ID=-1004459210142
set MP_ACCESS_TOKEN=APP_USR-5583372059840025-052821-7e16d5180e22b24c0799002489121e4c-166806987
set ENVIRONMENT=production

cd /d "%~dp0"

:: Inicia ngrok em janela separada
echo [1/3] Iniciando ngrok...
start "ngrok - WDO VIP" ngrok http 8000
timeout /t 4 /nobreak > nul

:: Pega URL publica do ngrok
for /f "tokens=*" %%i in ('python -c "import urllib.request,json; d=json.loads(urllib.request.urlopen(\"http://localhost:4040/api/tunnels\").read()); print([t[\"public_url\"] for t in d[\"tunnels\"] if t[\"proto\"]==\"https\"][0])" 2^>nul') do set NGROK_URL=%%i

if "%NGROK_URL%"=="" (
    echo [AVISO] ngrok nao detectado. Use http://localhost:8000 para testes locais.
    set RAILWAY_API_URL=http://localhost:8000
) else (
    echo [OK] URL publica: %NGROK_URL%
    set RAILWAY_API_URL=%NGROK_URL%
)

:: Cria/atualiza tabelas
echo.
echo [2/3] Atualizando banco de dados...
python -m database.migrate

:: Inicia API
echo.
echo [3/3] Iniciando API...
echo.
echo  Docs:          http://localhost:8000/docs
echo  URL publica:   %RAILWAY_API_URL%
echo.
echo  Configure o webhook do Mercado Pago:
echo  %RAILWAY_API_URL%/payments/webhook
echo.
echo  Adicione ao painel.py para ligar pelo Painel de Controle.
echo  ----------------------------------------

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
