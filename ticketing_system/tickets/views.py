from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import Ticket, Machine, Commentaire, DemandeIntervention, InterventionTechnique
from .models import OperatorProfile, Department
from .forms import TicketForm, TicketUpdateForm, CommentaireForm, MachineForm, FiltreTicketForm
from .forms import UserCreationForm, UserEditForm, OperatorProfileForm, DemandeInterventionForm, FiltreDemandeForm
from .forms import InterventionTechniqueForm, FiltreInterventionForm
from django.contrib.auth.models import User


def is_admin_or_supervisor(user):
    """Vérifie si l'utilisateur est admin ou superviseur."""
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, 'operatorprofile', None)
    return profile and profile.role == 'superviseur'


def is_admin(user):
    """Vérifie si l'utilisateur est admin."""
    return user.is_superuser or user.is_staff


def home(request):
    """Home view that redirects to dashboard if authenticated, otherwise to login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')


@login_required
def dashboard(request):
    # Statistiques générales
    total = Ticket.objects.count()
    ouverts = Ticket.objects.filter(statut='ouvert').count()
    en_cours = Ticket.objects.filter(statut='en_cours').count()
    resolus = Ticket.objects.filter(statut='resolu').count()
    critiques = Ticket.objects.filter(priorite='critique', statut__in=['ouvert', 'en_cours']).count()

    # Tickets récents
    tickets_recents = Ticket.objects.select_related('machine', 'cree_par', 'assigne_a').order_by('-date_creation')[:10]

    # Mes tickets assignés
    mes_tickets = Ticket.objects.filter(
        assigne_a=request.user,
        statut__in=['ouvert', 'en_cours', 'en_attente']
    ).select_related('machine').order_by('-priorite')[:5]

    # Stats par machine
    stats_machines = Machine.objects.filter(actif=True).annotate(
        nb_tickets=Count('tickets'),
        nb_ouverts=Count('tickets', filter=Q(tickets__statut__in=['ouvert', 'en_cours']))
    ).order_by('-nb_ouverts')[:5]

    # Stats par priorité
    stats_priorite = {
        'critique': Ticket.objects.filter(priorite='critique', statut__in=['ouvert', 'en_cours']).count(),
        'haute': Ticket.objects.filter(priorite='haute', statut__in=['ouvert', 'en_cours']).count(),
        'moyenne': Ticket.objects.filter(priorite='moyenne', statut__in=['ouvert', 'en_cours']).count(),
        'basse': Ticket.objects.filter(priorite='basse', statut__in=['ouvert', 'en_cours']).count(),
    }

    context = {
        'total': total, 'ouverts': ouverts, 'en_cours': en_cours,
        'resolus': resolus, 'critiques': critiques,
        'tickets_recents': tickets_recents,
        'mes_tickets': mes_tickets,
        'stats_machines': stats_machines,
        'stats_priorite': stats_priorite,
    }
    return render(request, 'tickets/dashboard.html', context)


@login_required
def ticket_list(request):
    tickets = Ticket.objects.select_related('machine', 'cree_par', 'assigne_a').all()
    # Restriction par département / profil utilisateur
    if not (request.user.is_superuser or request.user.is_staff):
        profile = getattr(request.user, 'operatorprofile', None)
        if profile and profile.department:
            allowed = profile.department.allowed_types_list()
            if allowed:
                tickets = tickets.filter(Q(type_panne__in=allowed) | Q(cree_par=request.user) | Q(assigne_a=request.user))
            else:
                tickets = tickets.filter(Q(cree_par=request.user) | Q(assigne_a=request.user))
        else:
            tickets = tickets.filter(Q(cree_par=request.user) | Q(assigne_a=request.user))
    form = FiltreTicketForm(request.GET)

    if form.is_valid():
        if form.cleaned_data.get('statut'):
            tickets = tickets.filter(statut=form.cleaned_data['statut'])
        if form.cleaned_data.get('priorite'):
            tickets = tickets.filter(priorite=form.cleaned_data['priorite'])
        if form.cleaned_data.get('categorie_ticket'):
            tickets = tickets.filter(categorie_ticket=form.cleaned_data['categorie_ticket'])
        if form.cleaned_data.get('machine'):
            tickets = tickets.filter(machine=form.cleaned_data['machine'])
        if form.cleaned_data.get('type_panne'):
            tickets = tickets.filter(type_panne=form.cleaned_data['type_panne'])
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            tickets = tickets.filter(
                Q(titre__icontains=q) | Q(description__icontains=q) | Q(machine__nom__icontains=q)
            )

    context = {'tickets': tickets, 'form': form, 'total': tickets.count()}
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related('machine', 'cree_par', 'assigne_a'), pk=pk)
    # Vérification d'accès
    if not (request.user.is_superuser or request.user.is_staff):
        profile = getattr(request.user, 'operatorprofile', None)
        allowed = []
        if profile and profile.department:
            allowed = profile.department.allowed_types_list()
        if not (ticket.type_panne in allowed or ticket.cree_par == request.user or ticket.assigne_a == request.user):
            messages.error(request, "Vous n'avez pas la permission de voir ce ticket.")
            return redirect('ticket_list')
    commentaires = ticket.commentaires.select_related('auteur').all()
    form_commentaire = CommentaireForm()

    if request.method == 'POST':
        form_commentaire = CommentaireForm(request.POST)
        if form_commentaire.is_valid():
            commentaire = form_commentaire.save(commit=False)
            commentaire.ticket = ticket
            commentaire.auteur = request.user
            commentaire.save()
            messages.success(request, "Commentaire ajouté.")
            return redirect('ticket_detail', pk=pk)

    context = {'ticket': ticket, 'commentaires': commentaires, 'form_commentaire': form_commentaire}
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.cree_par = request.user
            ticket.save()
            messages.success(request, f"Ticket #{ticket.pk} créé avec succès!")
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm(user=request.user)

    return render(request, 'tickets/ticket_form.html', {'form': form, 'action': 'Créer'})


@login_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    # Vérification d'accès basée sur le rôle
    if not (request.user.is_superuser or request.user.is_staff):
        profile = getattr(request.user, 'operatorprofile', None)
        if not (profile and profile.department):
            messages.error(request, "Votre compte n'est pas assigné à un département.")
            return redirect('ticket_list')
        allowed = profile.department.allowed_types_list()
        if profile.role == 'superviseur':
            if ticket.type_panne not in allowed:
                messages.error(request, "Vous n'avez pas la permission de modifier ce ticket.")
                return redirect('ticket_list')
        else:  # operateur
            if not (ticket.cree_par == request.user or ticket.assigne_a == request.user):
                messages.error(request, "Vous n'avez pas la permission de modifier ce ticket.")
                return redirect('ticket_list')
    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            if ticket.statut in ['resolu', 'ferme'] and not ticket.date_resolution:
                ticket.date_resolution = timezone.now()
            ticket.save()
            messages.success(request, f"Ticket #{ticket.pk} mis à jour.")
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = TicketUpdateForm(instance=ticket, user=request.user)

    return render(request, 'tickets/ticket_form.html', {'form': form, 'ticket': ticket, 'action': 'Modifier'})


@login_required
def ticket_change_statut(request, pk, statut):
    ticket = get_object_or_404(Ticket, pk=pk)
    statuts_valides = [s[0] for s in Ticket.STATUT_CHOICES]
    if statut in statuts_valides:
        ticket.statut = statut
        if statut in ['resolu', 'ferme']:
            ticket.date_resolution = timezone.now()
        ticket.save()
        messages.success(request, f"Statut changé en '{ticket.get_statut_display()}'")
    return redirect('ticket_detail', pk=pk)


@login_required
def machine_list(request):
    # Restreindre l'accès aux admins et superviseurs
    if not is_admin_or_supervisor(request.user):
        messages.error(request, "Vous n'avez pas la permission d'accéder à la liste des machines.")
        return redirect('ticket_list')
    
    machines = Machine.objects.annotate(
        nb_tickets=Count('tickets'),
        nb_ouverts=Count('tickets', filter=Q(tickets__statut__in=['ouvert', 'en_cours']))
    ).all()
    return render(request, 'tickets/machine_list.html', {'machines': machines})


@login_required
def machine_create(request):
    # Restreindre l'accès aux admins et superviseurs
    if not is_admin_or_supervisor(request.user):
        messages.error(request, "Vous n'avez pas la permission de créer une machine.")
        return redirect('ticket_list')
    
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save()
            messages.success(request, f"Machine '{machine.nom}' créée.")
            return redirect('machine_list')
    else:
        form = MachineForm()
    return render(request, 'tickets/machine_form.html', {'form': form, 'action': 'Ajouter'})


@login_required
def machine_edit(request, pk):
    # Restreindre l'accès aux admins et superviseurs
    if not is_admin_or_supervisor(request.user):
        messages.error(request, "Vous n'avez pas la permission de modifier une machine.")
        return redirect('ticket_list')
    
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Machine '{machine.nom}' mise à jour.")
            return redirect('machine_list')
    else:
        form = MachineForm(instance=machine)
    return render(request, 'tickets/machine_form.html', {'form': form, 'machine': machine, 'action': 'Modifier'})


# ============ Gestion des utilisateurs (Admin uniquement) ============

@login_required
def user_list(request):
    """Lister tous les utilisateurs avec leurs rôles et départements."""
    if not is_admin(request.user):
        messages.error(request, "Vous n'avez pas la permission d'accéder à la gestion des utilisateurs.")
        return redirect('dashboard')
    
    users = User.objects.filter(is_active=True).select_related('operatorprofile__department').order_by('username')
    context = {'users': users}
    return render(request, 'tickets/user_list.html', context)


@login_required
def user_create(request):
    """Créer un nouvel utilisateur avec son profil."""
    if not is_admin(request.user):
        messages.error(request, "Vous n'avez pas la permission de créer un utilisateur.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_form = OperatorProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Créer l'utilisateur
            user = user_form.save()
            
            # Mettre à jour le profil
            profile = user.operatorprofile
            profile.role = profile_form.cleaned_data['role']
            profile.department = profile_form.cleaned_data['department']
            profile.save()
            
            messages.success(request, f"Utilisateur '{user.username}' créé avec succès!")
            return redirect('user_list')
    else:
        user_form = UserCreationForm()
        profile_form = OperatorProfileForm()
    
    context = {'user_form': user_form, 'profile_form': profile_form, 'action': 'Créer'}
    return render(request, 'tickets/user_form.html', context)


@login_required
def user_edit(request, pk):
    """Modifier un utilisateur et son profil."""
    if not is_admin(request.user):
        messages.error(request, "Vous n'avez pas la permission de modifier un utilisateur.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, pk=pk)
    profile = user.operatorprofile
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = OperatorProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f"Utilisateur '{user.username}' mis à jour avec succès!")
            return redirect('user_list')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = OperatorProfileForm(instance=profile)
    
    context = {'user': user, 'user_form': user_form, 'profile_form': profile_form, 'action': 'Modifier'}
    return render(request, 'tickets/user_form.html', context)


@login_required
def user_delete(request, pk):
    """Supprimer un utilisateur (désactiver)."""
    if not is_admin(request.user):
        messages.error(request, "Vous n'avez pas la permission de supprimer un utilisateur.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, f"Utilisateur '{user.username}' supprimé (désactivé).")
        return redirect('user_list')
    
    context = {'user': user}
    return render(request, 'tickets/user_delete_confirm.html', context)


# ============ Vues pour les Demandes d'Intervention ============

@login_required
def demande_dashboard(request):
    """Dashboard principal pour les demandes d'intervention"""
    # Statistiques générales
    total = DemandeIntervention.objects.count()
    en_attente = DemandeIntervention.objects.filter(statut='en_attente').count()
    validees = DemandeIntervention.objects.filter(statut='validee').count()
    en_cours = DemandeIntervention.objects.filter(statut='en_cours').count()
    terminees = DemandeIntervention.objects.filter(statut='terminee').count()
    
    # Demandes récentes
    demandes_recentes = DemandeIntervention.objects.select_related(
        'machine'
    ).order_by('-date_creation')[:10]
    
    # Demandes par service
    stats_services = DemandeIntervention.objects.values('service_demandeur').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Demandes par nature d'anomalie
    stats_natures = DemandeIntervention.objects.values('nature_anomalie').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total': total, 'en_attente': en_attente, 'validees': validees,
        'en_cours': en_cours, 'terminees': terminees,
        'demandes_recentes': demandes_recentes,
        'stats_services': stats_services,
        'stats_natures': stats_natures,
    }
    return render(request, 'tickets/demande_dashboard.html', context)


@login_required
def demande_list(request):
    """Liste de toutes les demandes d'intervention avec filtres"""
    demandes = DemandeIntervention.objects.select_related('machine').all()
    form = FiltreDemandeForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('statut'):
            demandes = demandes.filter(statut=form.cleaned_data['statut'])
        if form.cleaned_data.get('nature_anomalie'):
            demandes = demandes.filter(nature_anomalie=form.cleaned_data['nature_anomalie'])
        if form.cleaned_data.get('service_demandeur'):
            demandes = demandes.filter(service_demandeur__icontains=form.cleaned_data['service_demandeur'])
        if form.cleaned_data.get('machine'):
            demandes = demandes.filter(machine=form.cleaned_data['machine'])
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            demandes = demandes.filter(
                Q(numero_demande__icontains=q) | 
                Q(description_anomalie__icontains=q) | 
                Q(demandeur__icontains=q) |
                Q(machine__nom__icontains=q)
            )
        if form.cleaned_data.get('type_intervention'):
            type_int = form.cleaned_data['type_intervention'] == 'True'
            demandes = demandes.filter(type_intervention=type_int)
    
    context = {'demandes': demandes, 'form': form, 'total': demandes.count()}
    return render(request, 'tickets/demande_list.html', context)


@login_required
def demande_detail(request, pk):
    """Détail d'une demande d'intervention"""
    demande = get_object_or_404(DemandeIntervention.objects.select_related('machine'), pk=pk)
    context = {'demande': demande}
    return render(request, 'tickets/demande_detail.html', context)


@login_required
def demande_create(request):
    """Créer une nouvelle demande d'intervention"""
    if request.method == 'POST':
        form = DemandeInterventionForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.save()
            messages.success(request, f"Demande '{demande.numero_demande}' créée avec succès!")
            return redirect('demande_detail', pk=demande.pk)
    else:
        form = DemandeInterventionForm()
    
    return render(request, 'tickets/demande_form.html', {'form': form, 'action': 'Créer'})


@login_required
def demande_edit(request, pk):
    """Modifier une demande d'intervention"""
    demande = get_object_or_404(DemandeIntervention, pk=pk)
    
    if request.method == 'POST':
        form = DemandeInterventionForm(request.POST, instance=demande)
        if form.is_valid():
            form.save()
            messages.success(request, f"Demande '{demande.numero_demande}' mise à jour.")
            return redirect('demande_detail', pk=demande.pk)
    else:
        form = DemandeInterventionForm(instance=demande)
    
    return render(request, 'tickets/demande_form.html', {'form': form, 'demande': demande, 'action': 'Modifier'})


@login_required
def demande_change_statut(request, pk, statut):
    """Changer le statut d'une demande d'intervention"""
    demande = get_object_or_404(DemandeIntervention, pk=pk)
    statuts_valides = [s[0] for s in DemandeIntervention.STATUT_CHOICES]
    if statut in statuts_valides:
        demande.statut = statut
        demande.save()
        messages.success(request, f"Statut changé en '{demande.get_statut_display()}'")
    return redirect('demande_detail', pk=pk)


# ============ Vues pour les Interventions Techniques ============

@login_required
def intervention_dashboard(request):
    """Dashboard principal pour les interventions techniques"""
    # Statistiques générales
    total = InterventionTechnique.objects.count()
    internes = InterventionTechnique.objects.filter(type_technicien='interne').count()
    externes = InterventionTechnique.objects.filter(type_technicien='externe').count()
    en_cours = InterventionTechnique.objects.filter(date_fin_intervention__isnull=True).count()
    terminees = InterventionTechnique.objects.filter(date_fin_intervention__isnull=False).count()
    
    # Interventions récentes
    interventions_recentes = InterventionTechnique.objects.select_related(
        'numero_demande', 'numero_demande__machine'
    ).filter(numero_demande__isnull=False).order_by('-date_creation')[:10]
    
    # Interventions par type de technicien
    stats_types = {
        'interne': internes,
        'externe': externes,
    }
    
    # Interventions par mois (approche simple sans ExtractMonth/ExtractYear)
    interventions_par_mois = {}
    interventions = InterventionTechnique.objects.filter(numero_demande__isnull=False).order_by('-date_creation')[:20]
    for intervention in interventions:
        mois_annee = intervention.date_creation.strftime('%m/%Y')
        if mois_annee not in interventions_par_mois:
            interventions_par_mois[mois_annee] = 0
        interventions_par_mois[mois_annee] += 1
    
    # Convertir en format similaire à stats_mois
    stats_mois = []
    for mois_annee, count in list(interventions_par_mois.items())[:6]:
        mois, annee = mois_annee.split('/')
        stats_mois.append({'mois': int(mois), 'annee': int(annee), 'count': count})
    
    context = {
        'total': total, 'internes': internes, 'externes': externes,
        'en_cours': en_cours, 'terminees': terminees,
        'interventions_recentes': interventions_recentes,
        'stats_types': stats_types,
        'stats_mois': stats_mois,
    }
    return render(request, 'tickets/intervention_dashboard.html', context)


@login_required
def viee_dashboard(request):
    """Dashboard pour le suivi de vie des équipements"""
    return render(request, 'tickets/viee_dashboard.html')


@login_required
def intervention_list(request):
    """Liste de toutes les interventions techniques avec filtres"""
    interventions = InterventionTechnique.objects.select_related(
        'numero_demande', 'numero_demande__machine'
    ).all()
    form = FiltreInterventionForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('type_technicien'):
            interventions = interventions.filter(type_technicien=form.cleaned_data['type_technicien'])
        if form.cleaned_data.get('numero_demande'):
            interventions = interventions.filter(
                numero_demande__numero_demande__icontains=form.cleaned_data['numero_demande']
            )
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            interventions = interventions.filter(
                Q(description_intervention__icontains=q) | 
                Q(nom_technicien__icontains=q) | 
                Q(nom_prestataire__icontains=q) |
                Q(numero_demande__machine__nom__icontains=q)
            )
        if form.cleaned_data.get('date_debut'):
            interventions = interventions.filter(
                date_prise_en_compte__gte=form.cleaned_data['date_debut']
            )
        if form.cleaned_data.get('date_fin'):
            interventions = interventions.filter(
                date_prise_en_compte__lte=form.cleaned_data['date_fin']
            )
    
    context = {'interventions': interventions, 'form': form, 'total': interventions.count()}
    return render(request, 'tickets/intervention_list.html', context)


@login_required
def intervention_detail(request, pk):
    """Détail d'une intervention technique"""
    intervention = get_object_or_404(
        InterventionTechnique.objects.select_related('numero_demande', 'numero_demande__machine'), 
        pk=pk
    )
    context = {'intervention': intervention}
    return render(request, 'tickets/intervention_detail.html', context)


@login_required
def intervention_create(request):
    """Créer une nouvelle intervention technique"""
    if request.method == 'POST':
        form = InterventionTechniqueForm(request.POST)
        if form.is_valid():
            intervention = form.save()
            messages.success(request, f"Intervention pour '{intervention.numero_demande.numero_demande}' créée avec succès!")
            return redirect('intervention_detail', pk=intervention.pk)
    else:
        form = InterventionTechniqueForm()
    
    return render(request, 'tickets/intervention_form.html', {'form': form, 'action': 'Créer'})


@login_required
def intervention_edit(request, pk):
    """Modifier une intervention technique"""
    intervention = get_object_or_404(InterventionTechnique, pk=pk)
    
    if request.method == 'POST':
        form = InterventionTechniqueForm(request.POST, instance=intervention)
        if form.is_valid():
            form.save()
            messages.success(request, f"Intervention pour '{intervention.numero_demande.numero_demande}' mise à jour.")
            return redirect('intervention_detail', pk=intervention.pk)
    else:
        form = InterventionTechniqueForm(instance=intervention)
    
    return render(request, 'tickets/intervention_form.html', {'form': form, 'intervention': intervention, 'action': 'Modifier'})


@login_required
def intervention_create_from_demande(request, demande_pk):
    """Créer une intervention technique à partir d'une demande"""
    demande = get_object_or_404(DemandeIntervention, pk=demande_pk)
    
    if request.method == 'POST':
        form = InterventionTechniqueForm(request.POST)
        # Pré-remplir le numéro de demande
        form.fields['numero_demande'].initial = demande
        if form.is_valid():
            intervention = form.save(commit=False)
            intervention.numero_demande = demande
            intervention.save()
            messages.success(request, f"Intervention pour '{demande.numero_demande}' créée avec succès!")
            return redirect('intervention_detail', pk=intervention.pk)
    else:
        form = InterventionTechniqueForm(initial={'numero_demande': demande})
    
    return render(request, 'tickets/intervention_form.html', {'form': form, 'action': 'Créer', 'demande': demande})

