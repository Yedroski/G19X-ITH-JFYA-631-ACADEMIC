@echo off
cd /d "%~dp0"
if exist ".venv311\Scripts\python.exe" goto install
py -3.11 -m venv .venv311
if not errorlevel 1 goto install
python -c "import sys; assert sys.version_info[:2] in ((3, 11), (3, 12)), 'Usa Python 3.11 o 3.12'"
if errorlevel 1 goto error
python -m venv .venv311
if errorlevel 1 goto error
:install
.venv311\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Instalacion completada. Usa iniciar_demo.bat o configura SQL Server.
pause
exit /b 0
:error
echo Fallo la instalacion. Revisa Python 3.11/3.12 y tu conexion.
pause
exit /b 1
