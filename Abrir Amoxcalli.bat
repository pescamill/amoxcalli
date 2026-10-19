@echo off
rem Doble clic en Windows: arranca Amoxcalli y lo abre en el navegador.
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul && set "PY=py -3"
%PY% -c "import sys; sys.exit(sys.version_info < (3, 11))" || goto nopython
echo Amoxcalli se abre en tu navegador (http://127.0.0.1:8766).
echo La primera vez prepara el analisis durante un minuto. Deja esta ventana abierta mientras lo usas; cierrala para salir.
%PY% -m nahuatl_local.platform serve --open
pause
exit /b
:nopython
echo Amoxcalli necesita Python 3.11 o mas reciente: https://www.python.org/downloads/
echo Al instalarlo, marca la casilla "Add python.exe to PATH".
pause
