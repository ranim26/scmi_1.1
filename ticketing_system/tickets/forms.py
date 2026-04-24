from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Machine, TicketSupport, OperatorProfile, Department, InterventionTechnique, SparePart

class TicketSupportForm(forms.ModelForm):

    fichiers = forms.FileField(
        label="Joindre des fichiers",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=False
    )
    SERVICE_CHOICES = [
        ('informatique', 'Informatique'),
        ('maintenance', 'Maintenance'),
        ('engineer', 'Engineer'),
    ]
    service_support = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        label="Service support",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    spare_part = forms.ModelChoiceField(
        queryset=SparePart.objects.filter(actif=True, quantite__gt=0),
        required=False,
        label="Réserver une pièce (optionnel)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TicketSupport
        fields = [
            'titre', 'service_support', 'categorie',
            'machine', 'priorite',
            'delai_souhaite', 'nature_probleme', 'description_probleme',
            'spare_part'
        ]
        widgets = {
            'date_ticket': forms.DateInput(attrs={'type': 'date'}),
            'heure_ticket': forms.TimeInput(attrs={'type': 'time'}),
            'delai_souhaite': forms.DateInput(attrs={'type': 'date'}),
            'description_probleme': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nature_probleme'].required = True
        self.fields['description_probleme'].required = True


class TicketSupportUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['machine'].queryset = Machine.objects.filter(actif=True)
        # Helper pour Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('statut', css_class='col-md-6'),
                Column('visa_demandeur', css_class='col-md-6'),
            ),
            Submit('submit', 'Mettre à jour', css_class='btn btn-primary'),
        )

    class Meta:
        model = TicketSupport
        fields = ['statut', 'visa_demandeur']


class MachineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
        self.fields['operator'].queryset = OperatorProfile.objects.none()
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['operator'].queryset = OperatorProfile.objects.filter(department_id=department_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.department:
            self.fields['operator'].queryset = OperatorProfile.objects.filter(department=self.instance.department)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nom', css_class='col-md-6'),
                Column('reference', css_class='col-md-6'),
            ),
            'localisation',
            'description',
            Row(
                Column('date_installation', css_class='col-md-6'),
                Column('actif', css_class='col-md-6'),
            ),
            Row(
                Column('department', css_class='col-md-6'),
                Column('operator', css_class='col-md-6'),
            ),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )

    class Meta:
        model = Machine
        fields = ['nom', 'reference', 'localisation', 'description', 'date_installation', 'actif', 'department', 'operator']
        widgets = {
            'date_installation': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }





class FiltreInterventionForm(forms.Form):
    type_technicien = forms.ChoiceField(
        choices=[('', 'Tous les types')] + InterventionTechnique.TYPE_TECHNICIEN_CHOICES,
        required=False, label='Type de technicien'
    )
    date_debut = forms.DateField(
        required=False, 
        label='Date de début',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False, 
        label='Date de fin',
        widget=forms.DateInput(attrs={'type': 'date'})
    )


class UserCreationForm(forms.ModelForm):
    is_admin = forms.BooleanField(label='Administrateur', required=False, help_text="Donne tous les droits d'administration.")
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmation mot de passe', widget=forms.PasswordInput)
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Département',
        empty_label='-- Choisir un département --'
    )
    role = forms.ChoiceField(
        choices=OperatorProfile.ROLE_CHOICES,
        label='Rôle',
        widget=forms.RadioSelect
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'role']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # Gérer le rôle admin
        if self.cleaned_data.get('is_admin'):
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
        if commit:
            user.save()
            # Créer ou mettre à jour le profil opérateur
            profile, created = OperatorProfile.objects.get_or_create(user=user)
            profile.department = self.cleaned_data.get('department')
            profile.role = self.cleaned_data.get('role', 'operateur')
            profile.save()
        return user


class UserUpdateForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Département',
        empty_label='-- Choisir un département --'
    )
    role = forms.ChoiceField(
        choices=OperatorProfile.ROLE_CHOICES,
        label='Rôle',
        widget=forms.RadioSelect
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'department', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.instance, 'operatorprofile'):
            self.fields['department'].initial = self.instance.operatorprofile.department
            self.fields['role'].initial = self.instance.operatorprofile.role

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Mettre à jour le profil opérateur
            profile, created = OperatorProfile.objects.get_or_create(user=user)
            profile.department = self.cleaned_data.get('department')
            profile.role = self.cleaned_data.get('role', 'operateur')
            profile.save()
        return user



# Formulaire pour choisir uniquement les machines de l'opérateur

# Formulaire complet pour OperatorProfile
class OperatorProfileForm(forms.ModelForm):
    class Meta:
        model = OperatorProfile
        fields = ['role', 'department', 'machines']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'machines': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'role': 'Rôle',
            'department': 'Département',
            'machines': "Machines associées à l'opérateur",
        }


class FiltreTicketSupportForm(forms.Form):
    """Formulaire de filtrage pour les tickets de support"""
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + TicketSupport.STATUT_CHOICES,
        required=False,
        label='Statut'
    )
    nature_anomalie = forms.ChoiceField(
        choices=[('', 'Toutes les natures')] + TicketSupport.NATURE_ANOMALIE_CHOICES,
        required=False,
        label='Nature anomalie'
    )
    service_demandeur = forms.CharField(
        required=False,
        label='Service demandeur',
        widget=forms.TextInput(attrs={'placeholder': 'Rechercher...'})
    )
    machine = forms.IntegerField(
        required=False,
        label='Machine',
        widget=forms.HiddenInput()
    )
    recherche = forms.CharField(
        required=False,
        label='Recherche',
        widget=forms.TextInput(attrs={'placeholder': 'Rechercher...'})
    )
    type_intervention = forms.ChoiceField(
        choices=[('', 'Tous les types'), ('True', 'Préventive'), ('False', 'Curative')],
        required=False,
        label='Type intervention'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si le paramètre machine est passé, vérifier qu'il existe
        machine_id = self.data.get('machine') or self.initial.get('machine')
        if machine_id:
            try:
                machine = Machine.objects.get(pk=machine_id)
                self.fields['machine'].initial = machine.pk
            except Machine.DoesNotExist:
                # Si la machine n'existe pas, ne pas filtrer
                pass


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

class SparePartForm(forms.ModelForm):
    machines = forms.ModelMultipleChoiceField(
        queryset=Machine.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Machines concernées"
    )

    class Meta:
        model = SparePart
        fields = ['nom', 'reference', 'machines', 'quantite']
        labels = {
            'nom': 'Nom de la pièce',
            'reference': 'Référence',
            'quantite': 'Quantité disponible',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
