@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Запуск Telegram-моста к Claude Code... (окно закрывать нельзя)
python bot.py
pause
