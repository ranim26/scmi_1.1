@echo off
echo ========================================
echo  Installation Systeme de Ticketing
echo ========================================
echo.


:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe!
    echo Telechargez Python sur https://www.python.org/downloads/
    pause
    exit /b 1
)


echo [1/4] Creation de l'environnement virtuel...
py -3.12 -m venv venv312
call venv312\Scripts\activate

echo [2/4] Installation des dependances...
pip install -r requirements.txt

echo [3/4] Creation de la base de donnees...
python manage.py makemigrations
python manage.py migrate

echo [4/4] Creation du superutilisateur admin...
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@industrie.com', 'admin123')"

echo [5/5] Chargement des donnees de demonstration...
python manage.py load_demo_data

echo.
echo ========================================
echo  Installation terminee avec succes!
echo  Lancez run.bat pour demarrer
echo ========================================
pause

:: Fix admin roles to ensure admin user always has correct privileges
python manage.py shell -c "from tickets.management.commands import fix_admin_roles; fix_admin_roles.run()"
