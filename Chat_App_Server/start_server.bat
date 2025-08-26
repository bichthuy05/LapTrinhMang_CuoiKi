@echo off
cd /d %~dp0\chat_app
python -m server.server_main
pause
