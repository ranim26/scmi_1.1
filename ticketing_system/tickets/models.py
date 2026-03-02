from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime


class Machine(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom de la machine")
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    localisation = models.CharField(max_length=200, verbose_name="Localisation / Zone")
    description = models.TextField(blank=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Active")
    date_installation = models.DateField(null=True, blank=True, verbose_name="Date d'installation")

    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.reference})"


class Ticket(models.Model):
    PRIORITE_CHOICES = [
        ('critique', '🔴 Critique'),
        ('haute', '🟠 Haute'),
        ('moyenne', '🟡 Moyenne'),
        ('basse', '🟢 Basse'),
    ]

    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('en_cours', 'En cours'),
        ('en_attente', 'En attente pièces'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé'),
    ]

    CATEGORIE_TICKET_CHOICES = [
        ('industrielle', '🏭 Panne industrielle'),
        ('bureautique', '🖥️ Panne bureautique'),
    ]

    TYPE_PANNE_CHOICES = [
        ('informatique', 'Informatique'),
        ('maintenance', 'Maintenance'),
        ('engineer', 'Ingénierie'),
    ]

    # Informations de base
    titre = models.CharField(max_length=300, verbose_name="Titre du ticket")
    description = models.TextField(verbose_name="Description de la panne")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=True, blank=True, related_name='tickets', verbose_name="Machine")
    categorie_ticket = models.CharField(max_length=15, choices=CATEGORIE_TICKET_CHOICES, default='industrielle', verbose_name="Catégorie de ticket")
    type_panne = models.CharField(max_length=20, choices=TYPE_PANNE_CHOICES, verbose_name="Type de panne")
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='moyenne', verbose_name="Priorité")
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='ouvert', verbose_name="Statut")

    # Personnes
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tickets_crees', verbose_name="Créé par")
    assigne_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assignes', verbose_name="Assigné à")

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    date_resolution = models.DateTimeField(null=True, blank=True, verbose_name="Date de résolution")

    # Informations techniques
    solution = models.TextField(blank=True, verbose_name="Solution appliquée")
    pieces_remplacees = models.TextField(blank=True, verbose_name="Pièces remplacées")
    temps_intervention = models.PositiveIntegerField(null=True, blank=True, verbose_name="Temps d'intervention (minutes)")

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-date_creation']

    def __str__(self):
        return f"#{self.pk} - {self.titre}"

    def get_priorite_class(self):
        classes = {
            'critique': 'danger',
            'haute': 'warning',
            'moyenne': 'info',
            'basse': 'success',
        }
        return classes.get(self.priorite, 'secondary')

    def get_statut_class(self):
        classes = {
            'ouvert': 'danger',
            'en_cours': 'warning',
            'en_attente': 'info',
            'resolu': 'success',
            'ferme': 'secondary',
        }
        return classes.get(self.statut, 'secondary')

    def duree_depuis_creation(self):
        delta = timezone.now() - self.date_creation
        heures = delta.seconds // 3600 + delta.days * 24
        if delta.days > 0:
            return f"{delta.days}j {(delta.seconds // 3600)}h"
        elif heures > 0:
            return f"{heures}h {(delta.seconds % 3600) // 60}min"
        else:
            return f"{delta.seconds // 60}min"


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
        ('operateur', 'Opérateur'),
        ('superviseur', 'Superviseur'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='operatorprofile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operateur')

    class Meta:
        verbose_name = 'Profil opérateur'
        verbose_name_plural = 'Profils opérateurs'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) - {self.department or 'Sans département'}"


# Crée automatiquement un OperatorProfile lors de la création d'un User (si non existant)
@receiver(post_save, sender=User)
def ensure_operator_profile(sender, instance, created, **kwargs):
    if created:
        OperatorProfile.objects.get_or_create(user=instance)

class Commentaire(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenu = models.TextField(verbose_name="Commentaire")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_creation']

    def __str__(self):
        return f"Commentaire de {self.auteur} sur #{self.ticket.pk}"


class DemandeIntervention(models.Model):
    """Modèle pour les demandes d'intervention"""
    
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
    numero_demande = models.CharField(max_length=50, unique=True, verbose_name="N° de demande")
    
    # Service et demandeur
    service_demandeur = models.CharField(max_length=200, verbose_name="Service demandeur")
    demandeur = models.CharField(max_length=200, verbose_name="Nom du demandeur")
    
    # Machine concernée
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Machine concernée")
    code_machine = models.CharField(max_length=100, verbose_name="Code machine")
    
    # Dates et heures
    date_demande = models.DateField(verbose_name="Date de demande")
    heure_demande = models.TimeField(verbose_name="Heure de demande")
    delai_souhaite = models.DateField(null=True, blank=True, verbose_name="Délai souhaité")
    
    # Type d'intervention
    type_intervention = models.BooleanField(default=False, verbose_name="Curative (décocher) / Préventive (cocher)")
    
    # Description de l'anomalie
    description_anomalie = models.TextField(verbose_name="Description de l'anomalie")
    nature_anomalie = models.CharField(max_length=20, choices=NATURE_ANOMALIE_CHOICES, verbose_name="Nature de l'anomalie")
    
    # Visa et statut
    visa_demandeur = models.CharField(max_length=200, blank=True, verbose_name="Visa du demandeur")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Demande d'intervention"
        verbose_name_plural = "Demandes d'intervention"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.numero_demande} - {self.machine.nom}"
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le numéro de demande si non fourni
        if not self.numero_demande:
            current_year = timezone.now().year
            current_month = timezone.now().month
            count = DemandeIntervention.objects.filter(
                date_creation__year=current_year,
                date_creation__month=current_month
            ).count()
            self.numero_demande = f"F_MATN_{current_month:02d}-{current_year}-{count+1:03d}"
        
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
    
    # Lien vers la demande d'intervention
    numero_demande = models.ForeignKey(DemandeIntervention, on_delete=models.CASCADE, null=True, verbose_name="N° de demande")
    
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
        return f"Intervention pour {self.numero_demande.numero_demande}"
    
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
