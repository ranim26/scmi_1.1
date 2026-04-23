# Import du modèle SMTPSettings pour l'inclure dans l'app
from .models_smtp import SMTPSettings
from django.db import models
from .models_ticket_file import TicketSupportFile
from django.contrib.auth.models import User

from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime


# --- Pièces de rechange (Spare Parts) ---
class SparePart(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom de la pièce")
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence pièce")
    description = models.TextField(blank=True, verbose_name="Description")
    machines = models.ManyToManyField('Machine', related_name='spare_parts', blank=True, verbose_name="Machines concernées")
    quantite = models.PositiveIntegerField(default=0, verbose_name="Quantité disponible")
    actif = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Pièce de rechange"
        verbose_name_plural = "Pièces de rechange"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.reference})"


class Machine(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom de la machine")
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    localisation = models.CharField(max_length=200, verbose_name="Localisation / Zone")
    description = models.TextField(blank=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Active")
    date_installation = models.DateField(null=True, blank=True, verbose_name="Date d'installation")
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Département associé")
    operator = models.ForeignKey('OperatorProfile', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Opérateur assigné")

    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.reference})"


class Department(models.Model):
    """Département (informatique / maintenance / engineer) avec types de panne autorisés.

    `allowed_types` stocke les clés `type_panne` autorisées, séparées par des virgules.
    """
    nom = models.CharField(max_length=100, unique=True)
    allowed_types = models.CharField(max_length=300, blank=True, help_text="Clés de `type_panne` séparées par des virgules")

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"

    def __str__(self):
        return self.nom

    def allowed_types_list(self):
        if not self.allowed_types:
            return []
        return [t.strip() for t in self.allowed_types.split(',') if t.strip()]


class OperatorProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('operateur', 'Opérateur'),
        ('superviseur', 'Superviseur'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='operatorprofile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operateur')
    machines = models.ManyToManyField('Machine', blank=True, verbose_name="Machines de l'opérateur")

    class Meta:
        verbose_name = 'Profil opérateur'
        verbose_name_plural = 'Profils opérateurs'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) - {self.department or 'Sans département'}"


# Crée automatiquement un OperatorProfile lors de la création d'un User (si non existant)
@receiver(post_save, sender=User)
def ensure_operator_profile(sender, instance, created, **kwargs):
    if created:
        role = 'admin' if instance.is_superuser and instance.is_staff else 'operateur'
        OperatorProfile.objects.get_or_create(user=instance, defaults={'role': role})

# --- SIGNALS TO KEEP OPERATOR/MACHINE ASSOCIATION IN SYNC ---
@receiver(post_save, sender=OperatorProfile)
def sync_operatorprofile_machines(sender, instance, **kwargs):
    # For each machine in operator's machines, set its operator FK if not already set
    for machine in instance.machines.all():
        if machine.operator != instance:
            machine.operator = instance
            machine.save(update_fields=["operator"])
    # For all machines where operator FK is this operator but not in M2M, remove FK
    Machine.objects.filter(operator=instance).exclude(id__in=instance.machines.values_list('id', flat=True)).update(operator=None)

@receiver(post_save, sender=Machine)
def sync_machine_operator(sender, instance, **kwargs):
    # If machine.operator is set, ensure it's in the operator's M2M
    if instance.operator:
        if not instance.operator.machines.filter(id=instance.id).exists():
            instance.operator.machines.add(instance)
    # If machine.operator is None, remove from all operator M2M
    else:
        for op in OperatorProfile.objects.filter(machines=instance):
            op.machines.remove(instance)

class TicketSupport(models.Model):
    titre = models.CharField(max_length=200, verbose_name="Titre du ticket", default="Sans titre")
    CATEGORIE_CHOICES = [
        ('industrielle', 'Industrielle'),
        ('informatique', 'Informatique'),
    ]
    categorie = models.CharField(max_length=30, choices=CATEGORIE_CHOICES, verbose_name="Catégorie", default='industrielle')
    type_panne = models.CharField(max_length=100, verbose_name="Type de panne", default="Non renseigné")
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
    ]
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, verbose_name="Priorité", default='moyenne')
    """Modèle pour les tickets de support"""
    
    NATURE_ANOMALIE_CHOICES = [
        ('mecanique', 'Mécanique'),
        ('electrique', 'Électrique'),
        ('hydraulique', 'Hydraulique'),
        ('pneumatique', 'Pneumatique'),
        ('informatique', 'Informatique'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    # Numéro de demande (généré automatiquement)
    numero_ticket = models.CharField(max_length=50, unique=True, verbose_name="N° de ticket")
    
    # Service et demandeur
    service_support = models.CharField(max_length=200, verbose_name="Service support")
    demandeur = models.CharField(max_length=200, verbose_name="Nom du demandeur")
    
    # Machine concernée
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Machine concernée")
    code_machine = models.CharField(max_length=100, verbose_name="Code machine")
    
    # Dates et heures
    date_ticket = models.DateField(verbose_name="Date du ticket")
    heure_ticket = models.TimeField(verbose_name="Heure du ticket")
    delai_souhaite = models.DateField(null=True, blank=True, verbose_name="Délai souhaité")
    
    # Type d'intervention
    type_support = models.BooleanField(default=False, verbose_name="Curative (décocher) / Préventive (cocher)")
    
    # Description de l'anomalie
    description_probleme = models.TextField(verbose_name="Description du problème")
    nature_probleme = models.CharField(max_length=20, choices=NATURE_ANOMALIE_CHOICES, verbose_name="Nature du problème")
    
    # Visa et statut
    visa_demandeur = models.CharField(max_length=200, blank=True, verbose_name="Visa du demandeur")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Ticket de support"
        verbose_name_plural = "Tickets de support"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.numero_ticket} - {self.machine.nom}"
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le numéro de ticket si non fourni
        if not self.numero_ticket:
            from django.db import transaction
            with transaction.atomic():
                # Verrouiller la table pour éviter les race conditions
                last_ticket = TicketSupport.objects.select_for_update().filter(
                    numero_ticket__startswith='T'
                ).order_by('-id').first()
                
                if last_ticket and last_ticket.numero_ticket[1:].isdigit():
                    last_number = int(last_ticket.numero_ticket[1:])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                # Boucle pour garantir l'unicité
                while True:
                    candidate = f"T{new_number:04d}"
                    if not TicketSupport.objects.filter(numero_ticket=candidate).exists():
                        self.numero_ticket = candidate
                        break
                    new_number += 1
        
        # Mettre à jour le code machine à partir de la machine
        if self.machine:
            self.code_machine = self.machine.reference
        super().save(*args, **kwargs)
    
    def get_statut_class(self):
        classes = {
            'en_attente': 'secondary',
            'validee': 'info',
            'en_cours': 'warning',
            'terminee': 'success',
            'annulee': 'danger',
        }
        return classes.get(self.statut, 'secondary')
    
    def get_type_intervention_display(self):
        return "Préventive" if self.type_intervention else "Curative"


class InterventionTechnique(models.Model):
    """Modèle pour les interventions techniques liées aux demandes"""
    
    TYPE_TECHNICIEN_CHOICES = [
        ('interne', 'Interne'),
        ('externe', 'Externe'),
    ]
    
    # Lien vers le ticket de support
    numero_ticket = models.ForeignKey(TicketSupport, on_delete=models.CASCADE, null=True, verbose_name="N° de ticket")
    
    # Type de technicien
    type_technicien = models.CharField(max_length=10, choices=TYPE_TECHNICIEN_CHOICES, verbose_name="Type de technicien")
    
    # Informations technicien (si interne)
    nom_technicien = models.CharField(max_length=200, blank=True, verbose_name="Nom du technicien maintenance")
    
    # Informations prestataire (si externe)
    nom_prestataire = models.CharField(max_length=200, blank=True, verbose_name="Nom du prestataire")
    nom_accompagnant = models.CharField(max_length=200, blank=True, verbose_name="Nom de l'accompagnant")
    
    # Dates et heures de prise en compte
    date_prise_en_compte = models.DateField(default=timezone.now, verbose_name="Date de prise en compte")
    heure_prise_en_compte = models.TimeField(default=timezone.now, verbose_name="Heure de prise en compte")
    
    # Description de l'intervention
    description_intervention = models.TextField(verbose_name="Description détaillée de l'intervention")
    
    # Dates et heures de fin
    date_fin_intervention = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    heure_fin_intervention = models.TimeField(null=True, blank=True, verbose_name="Heure de fin")
    
    # Visa et approbation
    visa_technicien = models.CharField(max_length=200, blank=True, verbose_name="Visa du technicien")
    approbation_fin = models.CharField(max_length=200, blank=True, verbose_name="Nom du demandeur approuvant la fin")
    visa_approbation = models.CharField(max_length=200, blank=True, verbose_name="Visa de l'approbateur")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Intervention technique"
        verbose_name_plural = "Interventions techniques"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Intervention pour {self.numero_ticket.numero_ticket}"
    
    def get_type_technicien_display_custom(self):
        """Retourne l'affichage du type de technicien"""
        return self.get_type_technicien_display()
    
    def duree_intervention(self):
        """Calcule la durée de l'intervention en heures"""
        if self.date_fin_intervention and self.heure_fin_intervention:
            debut = datetime.datetime.combine(self.date_prise_en_compte, self.heure_prise_en_compte)
            fin = datetime.datetime.combine(self.date_fin_intervention, self.heure_fin_intervention)
            duree = fin - debut
            heures = duree.total_seconds() / 3600
            return f"{heures:.1f} heures"
        return "En cours"


# Historique des modifications de ticket (à placer à la fin du fichier, niveau racine)

class TicketHistory(models.Model):
    ticket = models.ForeignKey('TicketSupport', on_delete=models.CASCADE, related_name='histories')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.user}: {self.action}"
