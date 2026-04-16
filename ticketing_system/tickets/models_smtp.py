from django.db import models

class SMTPSettings(models.Model):
    name = models.CharField(max_length=100, default="Default", unique=True, help_text="Nom du profil SMTP")
    host = models.CharField(max_length=255, help_text="Adresse du serveur SMTP")
    port = models.PositiveIntegerField(default=587, help_text="Port SMTP")
    username = models.CharField(max_length=255, help_text="Nom d'utilisateur SMTP")
    password = models.CharField(max_length=255, help_text="Mot de passe SMTP")
    use_tls = models.BooleanField(default=True, help_text="Utiliser TLS")
    use_ssl = models.BooleanField(default=False, help_text="Utiliser SSL")
    from_email = models.EmailField(help_text="Adresse email d'expédition")
    active = models.BooleanField(default=True, help_text="Profil SMTP actif")

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"