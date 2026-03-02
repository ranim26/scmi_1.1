@echo off
echo ========================================
echo  Demarrage Systeme de Ticketing
echo ========================================
call venv\Scripts\activate.bat
echo Serveur en cours sur http://127.0.0.1:8000
echo Appuyez Ctrl+C pour arreter
python manage.py runserver
pause
