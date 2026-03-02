from django.contrib import admin
from .models import Machine, Ticket, Commentaire
from .models import Department, OperatorProfile, DemandeIntervention, InterventionTechnique


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['nom', 'reference', 'localisation', 'actif', 'date_installation']
    list_filter = ['actif']
    search_fields = ['nom', 'reference', 'localisation']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['pk', 'titre', 'machine', 'priorite', 'statut', 'cree_par', 'assigne_a', 'date_creation']
    list_filter = ['statut', 'priorite', 'type_panne', 'machine']
    search_fields = ['titre', 'description', 'machine__nom']
    readonly_fields = ['date_creation', 'date_modification']


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'auteur', 'date_creation']
    readonly_fields = ['date_creation']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'allowed_types']
    search_fields = ['nom']


@admin.register(OperatorProfile)
class OperatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'role']
    list_filter = ['role', 'department']
    search_fields = ['user__username', 'user__email']


@admin.register(DemandeIntervention)
class DemandeInterventionAdmin(admin.ModelAdmin):
    list_display = [
        'numero_demande', 'service_demandeur', 'machine', 'demandeur', 
        'date_demande', 'nature_anomalie', 'statut', 'type_intervention'
    ]
    list_filter = [
        'statut', 'nature_anomalie', 'type_intervention', 
        'service_demandeur', 'date_demande'
    ]
    search_fields = [
        'numero_demande', 'demandeur', 'service_demandeur', 
        'machine__nom', 'description_anomalie'
    ]
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_demande', 'service_demandeur', 'demandeur', 'visa_demandeur', 'statut')
        }),
        ('Machine concernée', {
            'fields': ('machine', 'code_machine')
        }),
        ('Dates', {
            'fields': ('date_demande', 'heure_demande', 'delai_souhaite')
        }),
        ('Détails de l\'anomalie', {
            'fields': ('type_intervention', 'nature_anomalie', 'description_anomalie')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Si on modifie un objet existant
            readonly.append('numero_demande')  # Le numéro ne doit pas être modifiable
        return readonly


@admin.register(InterventionTechnique)
class InterventionTechniqueAdmin(admin.ModelAdmin):
    list_display = [
        'numero_demande', 'type_technicien', 'get_technicien_prestataire', 
        'date_prise_en_compte', 'date_fin_intervention', 'duree_intervention'
    ]
    list_filter = [
        'type_technicien', 'date_prise_en_compte', 'date_fin_intervention'
    ]
    search_fields = [
        'numero_demande__numero_demande', 'nom_technicien', 'nom_prestataire',
        'description_intervention', 'numero_demande__machine__nom'
    ]
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Lien vers la demande', {
            'fields': ('numero_demande',)
        }),
        ('Informations technicien', {
            'fields': ('type_technicien', 'nom_technicien', 'nom_prestataire', 'nom_accompagnant')
        }),
        ('Dates et heures', {
            'fields': ('date_prise_en_compte', 'heure_prise_en_compte', 
                      'date_fin_intervention', 'heure_fin_intervention')
        }),
        ('Description', {
            'fields': ('description_intervention',)
        }),
        ('Visa et approbation', {
            'fields': ('visa_technicien', 'approbation_fin', 'visa_approbation')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )
    
    def get_technicien_prestataire(self, obj):
        if obj.type_technicien == 'interne':
            return obj.nom_technicien or '-'
        else:
            return obj.nom_prestataire or '-'
    get_technicien_prestataire.short_description = 'Technicien/Prestataire'
    
    def duree_intervention(self, obj):
        return obj.duree_intervention()
    duree_intervention.short_description = 'Durée'
