from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Ticket, Commentaire, Machine, DemandeIntervention, OperatorProfile, Department, InterventionTechnique


class TicketForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self._form_user = user
        super().__init__(*args, **kwargs)
        # common field setup
        self.fields['assigne_a'].queryset = User.objects.filter(is_active=True)
        self.fields['assigne_a'].empty_label = "-- Non assigné --"
        self.fields['machine'].required = False

        # Limit type_panne choices based on user's department (non-admins)
        if user and not (user.is_superuser or user.is_staff):
            profile = getattr(user, 'operatorprofile', None)
            if profile and profile.department:
                allowed = profile.department.allowed_types_list()
                self.fields['type_panne'].choices = [c for c in Ticket.TYPE_PANNE_CHOICES if c[0] in allowed]
                # Auto-set type_panne to department name for new tickets and hide the field
                if profile.department.nom in [c[0] for c in Ticket.TYPE_PANNE_CHOICES]:
                    self.fields['type_panne'].initial = profile.department.nom
                    # For non-admin users the field should not be strictly required in the POST
                    self.fields['type_panne'].required = False
                    if profile.role == 'operateur':
                        from django.forms import HiddenInput
                        self.fields['type_panne'].widget = HiddenInput()
                    else:  # superviseur: show but read-only
                        self.fields['type_panne'].widget.attrs.update({'disabled': 'disabled'})
            else:
                # No department: make field empty and show message on clean
                self.fields['type_panne'].choices = []

        # crispy helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('titre', css_class='col-md-12'),
            ),
            Row(
                Column('categorie_ticket', css_class='col-md-6'),
                Column('machine', css_class='col-md-6'),
            ),
            Row(
                Column('type_panne', css_class='col-md-6'),
                Column('priorite', css_class='col-md-6'),
            ),
            Row(
                Column('assigne_a', css_class='col-md-12'),
            ),
            'description',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary btn-lg'),
        )

    class Meta:
        model = Ticket
        fields = ['titre', 'machine', 'categorie_ticket', 'type_panne', 'priorite', 'description', 'assigne_a']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    

    def clean(self):
        cleaned_data = super().clean()
        categorie = cleaned_data.get('categorie_ticket')
        machine = cleaned_data.get('machine')
        type_panne = cleaned_data.get('type_panne')
        user = getattr(self, '_form_user', None)

        # Validate that non-admin users can only create tickets for their department
        if user and not (user.is_superuser or user.is_staff):
            profile = getattr(user, 'operatorprofile', None)
            if not (profile and profile.department):
                raise forms.ValidationError("Votre compte n'est pas assigné à un département. Contactez un administrateur.")
            # if field was disabled in the form it may not be present in POST; default to department
            if not type_panne:
                type_panne = profile.department.nom
                cleaned_data['type_panne'] = type_panne
            allowed = profile.department.allowed_types_list()
            if type_panne and type_panne not in allowed:
                raise forms.ValidationError("Le type de panne sélectionné n'appartient pas à votre département.")
        
        if categorie == 'industrielle' and not machine:
            raise forms.ValidationError("La machine est obligatoire pour les pannes industrielles.")
        
        return cleaned_data


class TicketUpdateForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self._form_user = user
        super().__init__(*args, **kwargs)
        # common field setup
        self.fields['assigne_a'].queryset = User.objects.filter(is_active=True)
        self.fields['assigne_a'].empty_label = "-- Non assigné --"
        self.fields['machine'].required = False

        if user and not (user.is_superuser or user.is_staff):
            profile = getattr(user, 'operatorprofile', None)
            if profile and profile.department:
                allowed = profile.department.allowed_types_list()
                self.fields['type_panne'].choices = [c for c in Ticket.TYPE_PANNE_CHOICES if c[0] in allowed]
            else:
                self.fields['type_panne'].choices = []

    class Meta:
        model = Ticket
        fields = ['titre', 'machine', 'categorie_ticket', 'type_panne', 'priorite', 'statut', 
                  'description', 'assigne_a', 'solution', 'pieces_remplacees', 'temps_intervention']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'solution': forms.Textarea(attrs={'rows': 3}),
            'pieces_remplacees': forms.Textarea(attrs={'rows': 2}),
        }

    

    def clean(self):
        cleaned_data = super().clean()
        categorie = cleaned_data.get('categorie_ticket')
        machine = cleaned_data.get('machine')
        type_panne = cleaned_data.get('type_panne')
        user = getattr(self, '_form_user', None)

        if user and not (user.is_superuser or user.is_staff):
            profile = getattr(user, 'operatorprofile', None)
            if not (profile and profile.department):
                raise forms.ValidationError("Votre compte n'est pas assigné à un département. Contactez un administrateur.")
            if not type_panne:
                type_panne = profile.department.nom
                cleaned_data['type_panne'] = type_panne
            allowed = profile.department.allowed_types_list()
            if type_panne and type_panne not in allowed:
                raise forms.ValidationError("Le type de panne sélectionné n'appartient pas à votre département.")
        
        if categorie == 'industrielle' and not machine:
            raise forms.ValidationError("La machine est obligatoire pour les pannes industrielles.")
        
        return cleaned_data


class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ajouter un commentaire...'}),
        }
        labels = {'contenu': ''}


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['nom', 'reference', 'localisation', 'description', 'date_installation', 'actif']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_installation': forms.DateInput(attrs={'type': 'date'}),
        }


class FiltreTicketForm(forms.Form):
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Ticket.STATUT_CHOICES,
        required=False, label='Statut'
    )
    priorite = forms.ChoiceField(
        choices=[('', 'Toutes les priorités')] + Ticket.PRIORITE_CHOICES,
        required=False, label='Priorité'
    )
    categorie_ticket = forms.ChoiceField(
        choices=[('', 'Toutes les catégories')] + Ticket.CATEGORIE_TICKET_CHOICES,
        required=False, label='Catégorie'
    )
    machine = forms.ModelChoiceField(
        queryset=Machine.objects.filter(actif=True),
        required=False, empty_label="Toutes les machines", label='Machine'
    )
    recherche = forms.CharField(required=False, label='Recherche', 
                                 widget=forms.TextInput(attrs={'placeholder': 'Rechercher...'}))
    type_panne = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Ticket.TYPE_PANNE_CHOICES,
        required=False, label='Type de panne'
    )


class DemandeInterventionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuration des champs
        self.fields['machine'].queryset = Machine.objects.filter(actif=True)
        
        # Ne pas rendre les champs readonly, mais les pré-remplir via JavaScript
        self.fields['code_machine'].widget.attrs['placeholder'] = 'Sera rempli automatiquement'
        self.fields['numero_demande'].widget.attrs['placeholder'] = 'Sera généré automatiquement'
        
        # Helper pour Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero_demande', css_class='col-md-6'),
                Column('service_demandeur', css_class='col-md-6'),
            ),
            Row(
                Column('demandeur', css_class='col-md-6'),
                Column('visa_demandeur', css_class='col-md-6'),
            ),
            Row(
                Column('machine', css_class='col-md-6'),
                Column('code_machine', css_class='col-md-6'),
            ),
            Row(
                Column('date_demande', css_class='col-md-4'),
                Column('heure_demande', css_class='col-md-4'),
                Column('delai_souhaite', css_class='col-md-4'),
            ),
            Row(
                Column('type_intervention', css_class='col-md-6'),
                Column('nature_anomalie', css_class='col-md-6'),
            ),
            'description_anomalie',
            Submit('submit', 'Enregistrer la demande', css_class='btn btn-primary btn-lg'),
        )

    class Meta:
        model = DemandeIntervention
        fields = [
            'numero_demande', 'service_demandeur', 'demandeur', 'visa_demandeur',
            'machine', 'code_machine', 'date_demande', 'heure_demande', 
            'delai_souhaite', 'type_intervention', 'nature_anomalie', 
            'description_anomalie'
        ]
        widgets = {
            'date_demande': forms.DateInput(attrs={'type': 'date'}),
            'heure_demande': forms.TimeInput(attrs={'type': 'time'}),
            'delai_souhaite': forms.DateInput(attrs={'type': 'date'}),
            'description_anomalie': forms.Textarea(attrs={'rows': 4}),
            'type_intervention': forms.CheckboxInput(attrs={'data-toggle': 'toggle'}),
        }


class FiltreDemandeForm(forms.Form):
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + DemandeIntervention.STATUT_CHOICES,
        required=False, label='Statut'
    )
    nature_anomalie = forms.ChoiceField(
        choices=[('', 'Toutes les natures')] + DemandeIntervention.NATURE_ANOMALIE_CHOICES,
        required=False, label='Nature anomalie'
    )
    service_demandeur = forms.CharField(
        required=False, label='Service demandeur',
        widget=forms.TextInput(attrs={'placeholder': 'Filtrer par service...'})
    )
    machine = forms.ModelChoiceField(
        queryset=Machine.objects.filter(actif=True),
        required=False, empty_label="Toutes les machines", label='Machine'
    )
    recherche = forms.CharField(required=False, label='Recherche', 
                                 widget=forms.TextInput(attrs={'placeholder': 'Rechercher...'}))
    type_intervention = forms.ChoiceField(
        choices=[('', 'Tous les types'), ('True', 'Préventive'), ('False', 'Curative')],
        required=False, label='Type d\'intervention'
    )


# ============ Formulaires de gestion des utilisateurs ============

class UserCreationForm(forms.ModelForm):
    """Formulaire pour créer un nouvel utilisateur."""
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirm = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    """Formulaire pour modifier un utilisateur existant."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OperatorProfileForm(forms.ModelForm):
    """Formulaire pour modifier le profil d'opérateur (rôle et département)."""
    class Meta:
        model = OperatorProfile
        fields = ['role', 'department']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'role': 'Rôle',
            'department': 'Département',
        }


# ============ Formulaires pour les Interventions Techniques ============

class InterventionTechniqueForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuration des champs
        self.fields['numero_demande'].queryset = DemandeIntervention.objects.all()
        
        # Helper pour Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero_demande', css_class='col-md-12'),
            ),
            Row(
                Column('type_technicien', css_class='col-md-4'),
                Column('nom_technicien', css_class='col-md-8'),
            ),
            Row(
                Column('nom_prestataire', css_class='col-md-6'),
                Column('nom_accompagnant', css_class='col-md-6'),
            ),
            Row(
                Column('date_prise_en_compte', css_class='col-md-6'),
                Column('heure_prise_en_compte', css_class='col-md-6'),
            ),
            'description_intervention',
            Row(
                Column('date_fin_intervention', css_class='col-md-6'),
                Column('heure_fin_intervention', css_class='col-md-6'),
            ),
            Row(
                Column('visa_technicien', css_class='col-md-6'),
                Column('approbation_fin', css_class='col-md-6'),
            ),
            'visa_approbation',
            Submit('submit', 'Enregistrer l\'intervention', css_class='btn btn-primary btn-lg'),
        )

    class Meta:
        model = InterventionTechnique
        fields = [
            'numero_demande', 'type_technicien', 'nom_technicien', 'nom_prestataire', 
            'nom_accompagnant', 'date_prise_en_compte', 'heure_prise_en_compte',
            'description_intervention', 'date_fin_intervention', 'heure_fin_intervention',
            'visa_technicien', 'approbation_fin', 'visa_approbation'
        ]
        widgets = {
            'date_prise_en_compte': forms.DateInput(attrs={'type': 'date'}),
            'heure_prise_en_compte': forms.TimeInput(attrs={'type': 'time'}),
            'date_fin_intervention': forms.DateInput(attrs={'type': 'date'}),
            'heure_fin_intervention': forms.TimeInput(attrs={'type': 'time'}),
            'description_intervention': forms.Textarea(attrs={'rows': 4}),
            'type_technicien': forms.Select(attrs={'onchange': 'toggleTechnicienFields()'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        type_technicien = cleaned_data.get('type_technicien')
        nom_technicien = cleaned_data.get('nom_technicien')
        nom_prestataire = cleaned_data.get('nom_prestataire')
        
        if type_technicien == 'interne' and not nom_technicien:
            raise forms.ValidationError("Le nom du technicien est obligatoire pour un technicien interne.")
        
        if type_technicien == 'externe' and not nom_prestataire:
            raise forms.ValidationError("Le nom du prestataire est obligatoire pour un technicien externe.")
        
        return cleaned_data


class FiltreInterventionForm(forms.Form):
    type_technicien = forms.ChoiceField(
        choices=[('', 'Tous les types')] + InterventionTechnique.TYPE_TECHNICIEN_CHOICES,
        required=False, label='Type technicien'
    )
    numero_demande = forms.CharField(
        required=False, label='N° demande',
        widget=forms.TextInput(attrs={'placeholder': 'Filtrer par N° demande...'})
    )
    recherche = forms.CharField(
        required=False, label='Recherche',
        widget=forms.TextInput(attrs={'placeholder': 'Rechercher...'})
    )
    date_debut = forms.DateField(
        required=False, label='Date début',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False, label='Date fin',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

