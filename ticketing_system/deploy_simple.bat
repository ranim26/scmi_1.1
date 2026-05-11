@echo off
REM Script de déploiement simple pour Windows - Test local
REM Auteur: Assistant IA

echo ========================================
echo   Déploiement Django Local (Windows)
echo ========================================

REM Variables
set CURRENT_DIR=%~dp0
set PROJECT_NAME=ticketing_system

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

echo 🚀 Démarrage du serveur de développement...
echo 🌐 Votre site sera accessible sur: http://127.0.0.1:8000
echo 📝 Appuyez sur Ctrl+C pour arrêter le serveur
echo.

python manage.py runserver 127.0.0.1:8000
