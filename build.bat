@echo off
echo ==========================================
echo    DJ CamelTrack - Creador de EXE
echo ==========================================
echo.
echo Asegurate de haber instalado Python y marcado "Add Python to PATH"
echo durante la instalacion.
echo.
echo Paso 1: Instalando dependencias (incluyendo PyInstaller)...
pip install -r requirements.txt
echo.
echo Paso 2: Generando el archivo ejecutable...
pyinstaller --noconfirm --onedir --windowed --name "DJ CamelTrack" main.py
echo.
echo ==========================================
echo PROCESO COMPLETADO
echo Tu aplicacion se encuentra en la carpeta "dist\DJ CamelTrack"
echo ==========================================
pause
