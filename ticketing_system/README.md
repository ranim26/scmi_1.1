# Système de Ticketing Industriel - Guide d'Installation

## Structure du Projet
```
ticketing_system/
├── manage.py
├── requirements.txt
├── setup.bat              ← Lancer ce fichier en premier (Windows)
├── run.bat                ← Pour démarrer le serveur
├── ticketing_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── tickets/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── admin.py
    └── templates/tickets/
        ├── base.html
        ├── dashboard.html
        ├── ticket_list.html
        ├── ticket_detail.html
        └── ticket_form.html
```

## Installation (Windows 10/11)

1. Installer Python 3.10+ : https://www.python.org/downloads/
2. Double-cliquer sur `setup.bat`
3. Double-cliquer sur `run.bat`
4. Ouvrir : http://127.0.0.1:8000
5. Admin : http://127.0.0.1:8000/admin (admin / admin123)
