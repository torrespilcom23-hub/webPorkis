@echo off
REM ============================================================
REM  Granja Porkis - Iniciar servidor de desarrollo
REM  - Usa siempre el entorno virtual (venv) del proyecto
REM  - Si ya hay un servidor en el puerto 8000, NO abre otro;
REM    solo abre el navegador
REM ============================================================
cd /d D:\Proyectos\webPorkis

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo.
    echo  [AVISO] El servidor YA esta corriendo en http://127.0.0.1:8000
    echo  No se abrira un segundo servidor. Abriendo el navegador...
    echo.
    start http://127.0.0.1:8000/panel/
    pause
    exit /b 0
)

echo Iniciando servidor de Granja Porkis...
echo Cuando veas "Starting development server", entra a:
echo http://127.0.0.1:8000/panel/
echo.
echo Para detener el servidor: presiona Ctrl + C en esta ventana.
echo.
start "" /min cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8000/panel/"
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
