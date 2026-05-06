@echo off
REM Script de déploiement réseau pour Windows
REM Auteur: Assistant IA

echo ========================================
echo   Déploiement Django Réseau (Windows)
echo ========================================

REM Variables
set CURRENT_DIR=%~dp0
set PROJECT_NAME=ticketing_system

echo 🌐 Configuration pour accès réseau...

REM Obtenir l'adresse IP locale
echo 📡 Recherche de votre adresse IP locale...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set LOCAL_IP=%%b
)

if not defined LOCAL_IP (
    echo ❌ Impossible de trouver l'adresse IP locale
    echo Veuillez vérifier votre connexion réseau
    pause
    exit /b 1
)

echo ✅ Adresse IP trouvée: %LOCAL_IP%

REM Mettre à jour ALLOWED_HOSTS dans .env
echo 🔧 Mise à jour de ALLOWED_HOSTS...
powershell -Command "(Get-Content .env) -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=localhost,127.0.0.1,127.0.1.1,%LOCAL_IP%' | Set-Content .env"

echo 📦 Vérification de Python...
python --version
if %errorLevel% neq 0 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    pause
    exit /b 1
)

echo 📚 Installation des dépendances...
python -m pip install --upgrade pip
python -m pip install django gunicorn wfastcgi python-dotenv

if exist "%CURRENT_DIR%requirements.txt" (
    python -m pip install -r "%CURRENT_DIR%requirements.txt"
)

echo 🗄️ Configuration de la base de données...
python manage.py makemigrations
python manage.py migrate

echo 📦 Collection des fichiers statiques...
python manage.py collectstatic --noinput

echo 🔥 Configuration du firewall pour accès réseau...
netsh advfirewall firewall add rule name="Django Ticketing HTTP" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="Django Ticketing Network" dir=in action=allow protocol=TCP localport=8000 remoteip=localsubnet

echo.
echo 🚀 Démarrage du serveur réseau...
echo.
echo 🌐 Accès local: http://127.0.0.1:8000
echo 🌐 Accès réseau: http://%LOCAL_IP%:8000
echo 📝 Partagez l'adresse réseau avec d'autres ordinateurs sur le même réseau
echo 📝 Appuyez sur Ctrl+C pour arrêter le serveur
echo.

python manage.py runserver 0.0.0.0:8000
