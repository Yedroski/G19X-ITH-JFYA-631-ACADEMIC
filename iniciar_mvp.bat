@echo off
cd /d "%~dp0"
if not exist ".venv311\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat para preparar las dependencias.
    pause
    exit /b 1
)
.venv311\Scripts\python.exe main.py --demo
if errorlevel 1 (
    echo No se pudo iniciar la aplicacion. Revisa el mensaje anterior o ejecuta instalar.bat.
    pause
    exit /b 1
)
