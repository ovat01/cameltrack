@echo off
echo =========================================
echo Instalando dependencias necesarias...
echo =========================================
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo =========================================
echo Construyendo DJ CamelTrack...
echo =========================================
REM Usamos python -m PyInstaller para evitar problemas si PyInstaller no esta en el PATH
python -m PyInstaller --noconfirm --onedir --windowed --name "DJ CamelTrack" --add-data "genre_model.pkl;." --hidden-import sklearn.ensemble._forest --hidden-import sklearn.tree._classes main.py

echo.
echo =========================================
echo Copiando modelo a la carpeta dist...
echo =========================================
copy genre_model.pkl "dist\DJ CamelTrack\"
copy genre_model.pkl dist\

echo.
echo =========================================
echo Proceso completado. Revisa los mensajes arriba.
echo =========================================
pause
