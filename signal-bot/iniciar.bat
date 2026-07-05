@echo off
title Signal Bot
color 0A
cls

echo ============================================
echo        SIGNAL BOT - Iniciando...
echo ============================================
echo.

set BOT_DIR=C:\Users\Game-PC\signal-bot
set PYTHON=C:\Users\Game-PC\AppData\Local\Programs\Python\Python313\python.exe

echo [0/2] Encerrando processos antigos...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe /t >nul 2>&1
timeout /t 3 /nobreak >nul

echo [1/2] Iniciando Coletor (Scraper local - acessa Tipminer)...
start "Signal Bot - Coletor" cmd /k "title Coletor && cd /d %BOT_DIR% && %PYTHON% -m collector.main"
timeout /t 4 /nobreak >nul

echo [2/2] Iniciando Painel Web...
if exist "%BOT_DIR%\frontend\.next" rmdir /s /q "%BOT_DIR%\frontend\.next"
start "Signal Bot - Painel" cmd /k "title Painel Web && cd /d %BOT_DIR%\frontend && npm run dev"
timeout /t 8 /nobreak >nul

echo.
echo ============================================
echo   Tudo iniciado!
echo ============================================
echo.
echo   Coletor     : janela "Coletor" (scraper local)
echo   Bot Telegram: Railway (nuvem - sempre ativo 24/7)
echo   API         : Railway (nuvem - sempre ativa)
echo   Painel      : http://localhost:3000
echo.
echo   IMPORTANTE: O Bot Telegram roda no Railway automaticamente.
echo   Deixe esta janela com o Coletor aberta enquanto quiser
echo   que os sinais sejam coletados.
echo.
start "" "http://localhost:3000"

echo Pressione qualquer tecla para fechar esta janela.
echo O Coletor continua rodando na sua janela.
pause >nul
