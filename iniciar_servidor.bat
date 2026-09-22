@echo off
REM ============================================================
REM  Granja Porkis - Iniciar servidor de desarrollo
REM  - Escucha en todas las interfaces (0.0.0.0) para pruebas en LAN
REM  - Usa siempre el entorno virtual (venv) del proyecto
REM ============================================================
cd /d D:\Proyectos\webPorkis

set "PUERTO=8000"
set "LAN_IP=172.17.74.7"

netstat -ano | findstr ":%PUERTO% " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo.
    echo  [AVISO] El servidor YA esta corriendo en el puerto %PUERTO%
    echo  Local:  http://127.0.0.1:%PUERTO%/panel/
    echo  Red LAN: http://%LAN_IP%:%PUERTO%/panel/
    echo.
    start http://127.0.0.1:%PUERTO%/panel/
    pause
    exit /b 0
)

echo Iniciando servidor de Granja Porkis...
echo.
echo  En ESTE PC:
echo    http://127.0.0.1:%PUERTO%/panel/
echo.
echo  Desde OTRO PC en la misma red (misma Wi-Fi/LAN):
echo    http://%LAN_IP%:%PUERTO%/
echo    http://%LAN_IP%:%PUERTO%/panel/
echo.
echo  Si no conecta: permita el puerto %PUERTO% en el Firewall de Windows
echo  (ver README seccion "Pruebas en red local").
echo.
echo Para detener el servidor: Ctrl + C en esta ventana.
echo.
start "" /min cmd /c "timeout /t 4 >nul & start http://127.0.0.1:%PUERTO%/panel/"
venv\Scripts\python.exe manage.py runserver 0.0.0.0:%PUERTO%
