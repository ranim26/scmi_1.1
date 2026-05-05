# Guide de Déploiement Windows - Ticketing Industriel

Ce guide explique comment déployer votre projet Django sur Windows avec IIS ou Apache.

## Options de Déploiement sur Windows

### Option 1: IIS (Recommandé pour Windows Server)
- Intégré à Windows Server
- Interface graphique complète
- Support natif de FastCGI

### Option 2: Apache avec mod_wsgi
- Alternative open-source
- Configuration flexible
- Compatible avec XAMPP/WAMP

### Option 3: WSL (Windows Subsystem for Linux)
- Environnement Linux natif dans Windows
- Utilise les configurations Linux standard
- Idéal pour le développement

- Isolation des dépendances


- Windows 10/11 ou Windows Server
- Python 3.8+ installé
- IIS activé
- Permissions administrateur
# Exécuter en tant qu'administrateur
deploy_windows.bat
```

### Installation manuelle

#### 1. Activer IIS
```powershell
# Activer les fonctionnalités IIS
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer
Enable-WindowsOptionalFeature -Online -FeatureName IIS-CommonHttpFeatures
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpErrors
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpLogging
Enable-WindowsOptionalFeature -Online -FeatureName IIS-StaticContent
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpRedirect
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ASPNET45
```

#### 2. Installer Python et dépendances
```batch
# Installer Python depuis python.org
# Puis dans PowerShell (administrateur):
pip install virtualenv django wfastcgi gunicorn
wfastcgi-enable
```

#### 3. Configurer le projet
```batch
# Copier les fichiers
xcopy /E /I /Y . C:\inetpub\wwwroot\ticketing_system

# Créer l'environnement virtuel
cd C:\inetpub\wwwroot\ticketing_system
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
pip install gunicorn

# Configurer Django
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

#### 4. Configurer IIS
1. Ouvrir le Gestionnaire des services Internet (IIS)
2. Créer un nouveau site:
   - Nom: `ticketing_system`
   - Chemin: `C:\inetpub\wwwroot\ticketing_system`
   - Port: 80
3. Ajouter un mappage de handler:
   - Chemin: `*`
   - Verbe: `*`
   - Module: `FastCgiModule`
   - Exécutable: `C:\Python39\python.exe|C:\Python39\Scripts\wfastcgi.py`
4. Copier `web.config` dans le répertoire du projet

---

## Option 2: Déploiement avec Apache

- Apache 2.4+ (XAMPP/WAMP recommandé)
- Python 3.8+
- mod_wsgi pour Apache

```batch
# Télécharger et installer XAMPP depuis https://www.apachefriends.org/
# Ou Apache Lounge depuis https://www.apachelounge.com/
```

#### 2. Installer mod_wsgi
```batch
pip install mod_wsgi
mod_wsgi-express install-module
```

#### 3. Configurer Apache
Ajoutez le contenu de `apache_httpd.conf` à votre configuration Apache principale.

#### 4. Démarrer Apache
```batch
# Avec XAMPP
# Utiliser le panneau de contrôle XAMPP

# Manuellement
httpd.exe -k start
```

---

## Option 3: Déploiement avec WSL

```bash
# Activer WSL
wsl --install

# Installer Ubuntu
wsl --install -d Ubuntu

# Dans WSL
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
```

### Utiliser les configurations Linux standards
Suivez le guide `README_DEPLOYMENT.md` dans l'environnement WSL.

---

## Option 4: Déploiement avec Docker
### Créer Dockerfile
```dockerfile
FROM python:3.9-slim

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "ticketing_project.wsgi:application"]
```

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=localhost,127.0.0.1

  nginx:
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/static
    depends_on:
      - web
```

### Lancement
```batch
docker-compose up -d
```

---

## Configuration de l'Environnement

### Fichier .env
```env
SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,votredomaine.com
DATABASE_URL=sqlite:///db.sqlite3
```

### Permissions Windows
```batch
# Donner les permissions à IIS
icacls "C:\inetpub\wwwroot\ticketing_system" /grant "IIS_IUSRS:(OI)(CI)F"
icacls "C:\inetpub\wwwroot\ticketing_system" /grant "IUSR:(OI)(CI)F"
```


## Monitoring et Logs

### IIS
- Logs: `C:\inetpub\logs\LogFiles\`
- Interface: Gestionnaire IIS → Journaux

### Apache
- Logs: `C:\Apache24\logs\`
- Error log: `error.log`
- Access log: `access.log`

### Django
```batch
# Voir les logs Django
type C:\inetpub\wwwroot\ticketing_system\logs\slow_requests.log
```

---

## Sécurité

### Firewall Windows
# Autoriser les ports HTTP/HTTPS
netsh advfirewall firewall add rule name="HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS" dir=in action=allow protocol=TCP localport=443
```

### HTTPS avec IIS
1. Obtenir un certificat SSL
2. Lier le certificat au site IIS
3. Forcer HTTPS dans les paramètres IIS

---

## Dépannage

### Problèmes courants IIS

#### 500.19 - Erreur de configuration
```batch
# Vérifier les permissions
icacls "C:\inetpub\wwwroot\ticketing_system\web.config" /grant "IUSR:R"
```

#### 502.5 - Erreur FastCGI
```batch
# Vérifier wfastcgi
wfastcgi-enable
# Redémarrer IIS
iisreset
```

### Problèmes Apache

#### Module mod_wsgi non trouvé
```batch
# Installer la bonne version
pip install mod_wsgi-httpd
```

#### Permissions refusées
```batch
# Donner les permissions au répertoire
icacls "C:\wamp64\www\ticketing_system" /grant "Everyone:(OI)(CI)F"
```

---

## Maintenance

### Mise à jour du code
```batch
cd C:\inetpub\wwwroot\ticketing_system
git pull
.venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
iisreset
```

### Backup
```batch
# Backup de la base de données
copy "C:\inetpub\wwwroot\ticketing_system\db.sqlite3" "backup\db_%date:~-4,4%%date:~-7,2%%date:~-10,2%.sqlite3"

# Backup des fichiers
robocopy "C:\inetpub\wwwroot\ticketing_system" "backup\files_%date:~-4,4%%date:~-7,2%%date:~-10,2%" /E
```

---

## Support

Pour toute question:
1. Vérifiez les logs d'événements Windows
2. Consultez les logs IIS/Apache
3. Vérifiez les permissions des fichiers
4. Testez la configuration Python en local
