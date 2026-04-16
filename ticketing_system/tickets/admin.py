from django.contrib import admin
from .models_smtp import SMTPSettings

# Interface d'administration pour SMTPSettings

from django.urls import path
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection

class SMTPTestForm(forms.Form):
    email = forms.EmailField(label="Adresse email de test")

@admin.register(SMTPSettings)
class SMTPSettingsAdmin(admin.ModelAdmin):
    list_display = ("name", "host", "port", "username", "from_email", "use_tls", "use_ssl", "active")
    list_filter = ("active", "use_tls", "use_ssl")
    search_fields = ("name", "host", "username", "from_email")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/test/', self.admin_site.admin_view(self.test_smtp), name='tickets_smtpsettings_test'),
        ]
        return custom_urls + urls

    def test_smtp(self, request, pk):
        smtp = self.get_object(request, pk)
        if not smtp:
            self.message_user(request, "Profil SMTP introuvable.", level=messages.ERROR)
            return redirect('..')
        if request.method == 'POST':
            form = SMTPTestForm(request.POST)
            if form.is_valid():
                to_email = form.cleaned_data['email']
                try:
                    connection = get_connection(
                        host=smtp.host,
                        port=smtp.port,
                        username=smtp.username,
                        password=smtp.password,
                        use_tls=smtp.use_tls,
                        use_ssl=smtp.use_ssl,
                    )
                    email = EmailMessage(
                        subject="Test SMTP depuis Django",
                        body="Ceci est un email de test envoyé depuis l'interface d'administration.",
                        from_email=smtp.from_email,
                        to=[to_email],
                        connection=connection
                    )
                    email.send(fail_silently=False)
                    self.message_user(request, f"Email de test envoyé à {to_email} !", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"Erreur d'envoi : {e}", level=messages.ERROR)
                return redirect(f'../../')
        else:
            form = SMTPTestForm()
        context = dict(
            self.admin_site.each_context(request),
            title=f"Tester l'envoi SMTP ({smtp.name})",
            smtp=smtp,
            form=form,
        )
        return render(request, "admin/tickets/test_smtp.html", context)
from django.contrib import admin
from .models import Machine, Department, OperatorProfile, TicketSupport, InterventionTechnique
from .models import Machine, TicketSupport, InterventionTechnique, OperatorProfile, Department, TicketHistory
@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ("ticket", "user", "action", "date")
    search_fields = ("ticket__numero_ticket", "user__username", "action", "details")
    list_filter = ("action", "date")


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['nom', 'reference', 'localisation', 'actif', 'date_installation']
    list_filter = ['actif']
    search_fields = ['nom', 'reference', 'localisation']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'allowed_types']
    search_fields = ['nom']


@admin.register(OperatorProfile)
class OperatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'role']
    list_filter = ['role', 'department']
    search_fields = ['user__username', 'user__email']


@admin.register(TicketSupport)
class TicketSupportAdmin(admin.ModelAdmin):
    list_display = [
        'numero_ticket', 'service_support', 'machine', 'demandeur', 
        'date_ticket', 'nature_probleme', 'statut', 'type_support'
    ]
    list_filter = [
        'statut', 'nature_probleme', 'type_support', 
        'service_support', 'date_ticket'
    ]
    search_fields = [
        'numero_ticket', 'demandeur', 'service_support', 
        'machine__nom', 'description_probleme'
    ]
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_ticket', 'service_support', 'demandeur', 'visa_demandeur', 'statut')
        }),
        ('Machine concernée', {
            'fields': ('machine', 'code_machine')
        }),
        ('Dates', {
            'fields': ('date_ticket', 'heure_ticket', 'delai_souhaite')
        }),
        ('Détails du problème', {
            'fields': ('type_support', 'nature_probleme', 'description_probleme')
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
        'numero_ticket', 'type_technicien', 'get_technicien_prestataire', 
        'date_prise_en_compte', 'date_fin_intervention', 'duree_intervention'
    ]
    list_filter = [
        'type_technicien', 'date_prise_en_compte', 'date_fin_intervention'
    ]
    search_fields = [
        'numero_ticket__numero_ticket', 'nom_technicien', 'nom_prestataire',
        'description_intervention', 'numero_ticket__machine__nom'
    ]
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Lien vers le ticket', {
            'fields': ('numero_ticket',)
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
