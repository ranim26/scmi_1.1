@echo off
REM Script de déploiement pour Windows - Django avec IIS/Apache
REM Auteur: Assistant IA
REM Date: %date%

echo ========================================
echo   Déploiement Django sur Windows
echo ========================================

REM Vérification des privilèges administrateur
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Ce script doit être exécuté en tant qu'administrateur
    pause
    exit /b 1
)

REM Variables
set PROJECT_PATH=C:\inetpub\wwwroot\ticketing_system
set PYTHON_PATH=C:\Python39
set PROJECT_NAME=ticketing_system
set CURRENT_DIR=%~dp0

echo 📦 Installation des dépendances...

REM Installation de Python si nécessaire
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo 🐍 Installation de Python...
    REM Télécharger et installer Python depuis python.org
    start https://www.python.org/downloads/windows/
    echo Veuillez installer Python manuellement, puis relancer ce script.
    pause
    exit /b 1
)

REM Installation de pip si nécessaire
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 📚 Installation de pip...
    python -m ensurepip --upgrade
)

REM Mise à jour de pip
python -m pip install --upgrade pip

REM Installation des dépendances Python
echo 📚 Installation des dépendances Python...
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m pip install django
python -m pip install gunicorn
python -m pip install wfastcgi
if exist "%CURRENT_DIR%requirements.txt" (
    python -m pip install -r "%CURRENT_DIR%requirements.txt"
) else (
    echo ⚠️ Fichier requirements.txt non trouvé, utilisation des dépendances par défaut
)

REM Configuration wfastcgi
echo ⚙️ Configuration wfastcgi...
wfastcgi-enable

REM Création du répertoire du projet
echo 📁 Création du répertoire du projet...
if not exist "%PROJECT_PATH%" (
    mkdir "%PROJECT_PATH%"
    mkdir "%PROJECT_PATH%\logs"
    mkdir "%PROJECT_PATH%\media"
)

REM Copie des fichiers du projet
echo 📋 Copie des fichiers du projet...
if not exist "%PROJECT_PATH%" (
    mkdir "%PROJECT_PATH%"
)
xcopy /E /I /Y "%CURRENT_DIR%*" "%PROJECT_PATH%"

REM Création de l'environnement virtuel
echo 🐍 Création de l'environnement virtuel...
cd /d "%PROJECT_PATH%"
if not exist ".venv" (
    python -m venv .venv
)

REM Activation de l'environnement virtuel et installation
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

REM Configuration de la base de données
echo 🗄️ Configuration de la base de données...
python manage.py makemigrations
python manage.py migrate

REM Collection des fichiers statiques
echo 📦 Collection des fichiers statiques...
python manage.py collectstatic --noinput

REM Configuration IIS
echo 🌐 Configuration IIS...
REM Vérifier si IIS est installé
if not exist "%windir%\system32\inetsrv\appcmd.exe" (
    echo ❌ IIS n'est pas installé. Veuillez l'installer manuellement:
    echo 1. Panneau de configuration ^> Programmes ^> Activer ou désactiver des fonctionnalités Windows
    echo 2. Cochez "Internet Information Services"
    echo 3. Développez et cochez "Outils de gestion Web" ^> "Console de gestion IIS"
    echo 4. Cliquez sur OK et redémarrez
    pause
) else (
    echo ✅ IIS est déjà installé
    
    REM Configuration du site IIS
    echo 📋 Configuration du site IIS...
    %windir%\system32\inetsrv\appcmd.exe add site /name:"%PROJECT_NAME%" /physicalPath:"%PROJECT_PATH%" /bindings:http/*:80:
    
    REM Configuration de l'application pool
    echo 🏊 Configuration du pool d'applications...
    %windir%\system32\inetsrv\appcmd.exe add apppool /name:"%PROJECT_NAME%" /processModel.identityType:ApplicationPoolIdentity
    %windir%\system32\inetsrv\appcmd.exe set app "%PROJECT_NAME%/" /applicationPool:"%PROJECT_NAME%"
)

REM Configuration du firewall
echo 🔥 Configuration du firewall...
netsh advfirewall firewall add rule name="Django Ticketing" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="Django Ticketing HTTPS" dir=in action=allow protocol=TCP localport=443

REM Création du service Windows pour Gunicorn (optionnel)
echo 🚀 Création du service Gunicorn...
sc create "DjangoTicketing" binPath= "cmd /c 'cd /d %PROJECT_PATH% && .venv\Scripts\gunicorn.exe --config gunicorn.conf.py ticketing_project.wsgi:application'" start= auto

echo.
echo ✅ Déploiement terminé avec succès!
echo.
echo 🌐 Votre site est accessible sur: http://localhost
echo.
echo 📝 Prochaines étapes:
echo    1. Configurez votre nom de domaine dans IIS
echo    2. Mettez à jour ALLOWED_HOSTS dans .env
echo    3. Configurez HTTPS si nécessaire
echo    4. Testez l'application
echo.
pause
