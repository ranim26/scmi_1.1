from django.db import models

class TicketSupportFile(models.Model):
    ticket = models.ForeignKey('TicketSupport', on_delete=models.CASCADE, related_name='fichiers')
    fichier = models.FileField(upload_to='tickets/files/')
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fichier.name
