ticketing_system/

# Système de Ticketing Industriel

## Présentation
Ce projet est une application web de gestion de tickets de support pour un environnement industriel, développée avec Django 4.2. Elle permet la gestion des machines, des tickets de support, des pièces détachées, des interventions techniques, des notifications et des utilisateurs (opérateurs, superviseurs, administrateurs).

## Structure du Projet
```
ticketing_system/
├── manage.py
├── requirements.txt
├── setup.bat              ← Lancer ce fichier en premier (Windows)
├── run.bat                ← Pour démarrer le serveur
├── db.sqlite3             ← Base de données SQLite (par défaut)
├── ticketing_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tickets/
│   ├── __init__.py
│   ├── admin.py
│   ├── forms.py
│   ├── middleware.py
│   ├── models.py
│   ├── models_smtp.py
│   ├── models_ticket_file.py
│   ├── urls.py
│   ├── views.py
│   ├── views_ticket_history.py
│   ├── management/
│   │   └── commands/      ← Commandes de gestion personnalisées
│   ├── migrations/
│   └── templates/
│       └── tickets/
│           ├── base.html
│           ├── dashboard.html
│           ├── ...
├── static/                ← Fichiers statiques (css, js, img)
├── media/                 ← Fichiers uploadés (pièces, tickets)
└── venv312/               ← Environnement virtuel Python (optionnel)
```

## Installation (Windows 10/11)

1. Installer Python 3.10+ : https://www.python.org/downloads/
2. Double-cliquer sur `setup.bat` pour installer les dépendances (pip, venv, requirements.txt).
3. Double-cliquer sur `run.bat` pour démarrer le serveur Django.
4. Accéder à l'application : http://127.0.0.1:8000
5. Accès admin : http://127.0.0.1:8000/admin (login: `admin` / mot de passe: `admin123` par défaut)

## Dépendances principales

Voir `requirements.txt` :

```
asgiref==3.11.1
crispy-bootstrap5==0.7
Django==4.2.30
django-crispy-forms==2.1
pillow==12.2.0
python-dotenv==1.0.0
reportlab==4.0.4
sqlparse==0.5.5
tzdata==2026.1
```

## Fonctionnalités principales

- **Gestion des tickets de support** (création, suivi, historique, priorités, statuts)
- **Gestion des machines** (création, activation/désactivation, affectation à des opérateurs)
- **Gestion des pièces détachées** (stock, réservation, alertes de stock critique)
- **Gestion des interventions techniques** (interne/externe, durée, validation)
- **Notifications d'alerte** (nouveau ticket, ticket critique, machine inactive, intervention terminée)
- **Gestion des utilisateurs** (profils opérateur, superviseur, admin, affectation de rôles et de machines)
- **Historique des actions** (modifications, interventions, réservations)
- **Fichiers attachés aux tickets** (upload, gestion)
- **Tableaux de bord dynamiques** (statistiques, alertes, graphiques)
- **Sécurité et permissions** (authentification, rôles, middleware de requêtes lentes)

## Modèles principaux

- **UserProfile / OperatorProfile** : profils utilisateurs et opérateurs (rôle, département, machines)
- **Machine** : machines industrielles (nom, référence, localisation, manuel, opérateur)
- **SparePart** : pièces détachées (nom, référence, stock, machines concernées)
- **TicketSupport** : tickets de support (catégorie, type, priorité, machine, description, statut, pièce réservée)
- **InterventionTechnique** : interventions techniques liées à un ticket (interne/externe, technicien, durée, validation)
- **NotificationAlert** : notifications d'alerte pour admins/superviseurs
- **StockReservation** : réservations de pièces détachées pour un ticket
- **TicketHistory** : historique des actions sur un ticket
- **SMTPSettings** : configuration SMTP pour l'envoi d'emails
- **TicketSupportFile** : fichiers attachés à un ticket

## Configuration et Personnalisation

- **Paramètres principaux** : voir `ticketing_project/settings.py` (base de données, statiques, médias, sécurité, CORS, logging)
- **Middleware de requêtes lentes** : `tickets/middleware.py` (log les requêtes > 200ms en DEBUG)
- **Commandes de gestion personnalisées** : `tickets/management/commands/`
- **Traduction** : `LANGUAGE_CODE = 'fr-fr'`, `TIME_ZONE = 'Europe/Paris'`

## Utilisation rapide

1. Créez des utilisateurs via l'admin ou la commande de gestion.
2. Ajoutez des machines, pièces détachées et utilisateurs opérateurs/superviseurs.
3. Les opérateurs créent des tickets, réservent des pièces, suivent l'avancement.
4. Les superviseurs/admins valident, affectent, clôturent les tickets et reçoivent des notifications.

## Sécurité & Conseils

- Changez la clé secrète et le mot de passe admin en production !
- Activez le mode production (`DEBUG = False`) et configurez les hôtes autorisés.
- Sauvegardez régulièrement la base de données (`db.sqlite3`).

## Auteurs & Contact

Développé par l'équipe maintenance industrielle.
Contact : [à personnaliser]
