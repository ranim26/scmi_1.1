from django.core.mail import EmailMessage, get_connection
from .models_smtp import SMTPSettings
# Imports principaux
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Machine, TicketSupport, InterventionTechnique, OperatorProfile, Department, SparePart
from .forms import UserEditForm, MachineForm, TicketSupportForm, TicketSupportUpdateForm, UserCreationForm, UserUpdateForm, OperatorProfileForm, FiltreTicketSupportForm, SparePartForm

# --- Pièces de rechange par machine ---
from django.contrib.auth.decorators import login_required

@login_required
def machine_spare_parts_view(request):
    machines = Machine.objects.prefetch_related('spare_parts').all()
    return render(request, 'tickets/machine_spare_parts.html', {'machines': machines})

@login_required
def add_spare_part(request):
    if request.method == 'POST':
        form = SparePartForm(request.POST)
        if form.is_valid():
            spare_part = form.save()
            # form.save_m2m()  # Not needed, handled by ModelForm save()
            messages.success(request, 'Pièce de rechange ajoutée avec succès.')
            return redirect('machine_spare_parts')
    else:
        form = SparePartForm()
    return render(request, 'tickets/add_spare_part.html', {'form': form})

# Vue pour choisir les machines de l'opérateur
@login_required
def choisir_machines(request):
    profile = getattr(request.user, 'operatorprofile', None)
    if not profile or profile.role != 'operateur':
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = OperatorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos machines ont été enregistrées.")
            return redirect('dashboard')
    else:
        form = OperatorProfileForm(instance=profile)

    return render(request, 'tickets/choisir_machines.html', {'form': form})
    """Vérifie si l'utilisateur est admin ou superviseur."""
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, 'operatorprofile', None)
    return profile and profile.role == 'superviseur'


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
    # --- Calculs pour les variations dynamiques ---
    from datetime import timedelta
    now = timezone.now()

    # (ticket_base_qs is set below, then we do calculations)

    # Now that ticket_base_qs is defined and all early returns are handled, do dynamic calculations
    last_week_start = now - timedelta(days=now.weekday() + 7)
    last_week_end = last_week_start + timedelta(days=6)
    yesterday = now - timedelta(days=1)

    opened_this_week = ticket_base_qs.filter(date_creation__gte=now - timedelta(days=now.weekday())).count() if 'ticket_base_qs' in locals() else 0
    opened_last_week = ticket_base_qs.filter(date_creation__date__gte=last_week_start.date(), date_creation__date__lte=last_week_end.date()).count() if 'ticket_base_qs' in locals() else 0
    if opened_last_week:
        opened_pct = round(100 * (opened_this_week - opened_last_week) / opened_last_week)
    else:
        opened_pct = 100 if opened_this_week else 0

    resolved_this_week = ticket_base_qs.filter(statut='terminee', date_modification__gte=now - timedelta(days=now.weekday())).count() if 'ticket_base_qs' in locals() else 0
    resolved_last_week = ticket_base_qs.filter(statut='terminee', date_modification__date__gte=last_week_start.date(), date_modification__date__lte=last_week_end.date()).count() if 'ticket_base_qs' in locals() else 0
    if resolved_last_week:
        resolved_pct = round(100 * (resolved_this_week - resolved_last_week) / resolved_last_week)
    else:
        resolved_pct = 100 if resolved_this_week else 0

    critiques_today = ticket_base_qs.filter(priorite='haute', date_creation__date=now.date()).count() if 'ticket_base_qs' in locals() else 0
    critiques_yesterday = ticket_base_qs.filter(priorite='haute', date_creation__date=yesterday.date()).count() if 'ticket_base_qs' in locals() else 0
    critiques_diff = critiques_today - critiques_yesterday

    user = request.user
    profile = getattr(user, 'operatorprofile', None)
    if is_admin_or_supervisor(user):
        if profile and profile.role == 'superviseur' and profile.department:
            machine_base_qs = Machine.objects.filter(department=profile.department)
            ticket_base_qs = TicketSupport.objects.filter(machine__department=profile.department)
            intervention_base_qs = InterventionTechnique.objects.filter(numero_ticket__machine__department=profile.department)
        else:
            machine_base_qs = Machine.objects.all()
            ticket_base_qs = TicketSupport.objects.all()
            intervention_base_qs = InterventionTechnique.objects.all()
    else:
        if not profile:
            messages.error(request, "Aucun profil opérateur trouvé.")
            return redirect('dashboard')
        # Redirect to choisir_machines if operator has no machines
        if profile.machines.count() == 0:
            messages.info(request, "Veuillez sélectionner vos machines pour commencer.")
            return redirect('choisir_machines')
        machine_base_qs = profile.machines.all()
        ticket_base_qs = TicketSupport.objects.filter(machine__in=machine_base_qs)
        intervention_base_qs = InterventionTechnique.objects.filter(numero_ticket__machine__in=machine_base_qs)

    total_tickets = ticket_base_qs.count()
    tickets_en_attente = ticket_base_qs.filter(statut='en_attente').count()
    tickets_en_cours = ticket_base_qs.filter(statut='en_cours').count()
    tickets_terminees = ticket_base_qs.filter(statut='terminee').count()
    tickets_validees = ticket_base_qs.filter(statut='validee').count()
    tickets_annulees = ticket_base_qs.filter(statut='annulee').count()

    search_query = request.GET.get('search', '').strip()
    tickets_recents_qs = ticket_base_qs.select_related('machine').order_by('-date_creation')
    if search_query:
        tickets_recents_qs = tickets_recents_qs.filter(
            Q(numero_ticket__icontains=search_query) |
            Q(titre__icontains=search_query) |
            Q(machine__nom__icontains=search_query)
        )
    tickets_recents = tickets_recents_qs[:5]

    stats_machines = machine_base_qs.filter(actif=True).annotate(
        nb_tickets=Count('ticketsupport'),
        nb_tickets_ouverts=Count('ticketsupport', filter=Q(ticketsupport__statut__in=['en_attente', 'validee', 'en_cours']))
    ).order_by('-nb_tickets_ouverts')[:5]

    total_interventions = intervention_base_qs.count()
    interventions_ce_mois = intervention_base_qs.filter(
        date_prise_en_compte__year=timezone.now().year,
        date_prise_en_compte__month=timezone.now().month
    ).count()

    search_machine = request.GET.get('search_machine', '').strip()
    all_machines_qs = machine_base_qs.annotate(
        nb_tickets=Count('ticketsupport', distinct=True),
        nb_ouverts=Count('ticketsupport', filter=Q(ticketsupport__statut__in=['en_attente', 'validee', 'en_cours']), distinct=True),
        nb_annulees=Count('ticketsupport', filter=Q(ticketsupport__statut='annulee'), distinct=True)
    )
    if search_machine:
        all_machines_qs = all_machines_qs.filter(
            Q(nom__icontains=search_machine) |
            Q(reference__icontains=search_machine) |
            Q(localisation__icontains=search_machine) |
            Q(department__nom__icontains=search_machine)
        )
    all_machines_qs = all_machines_qs.order_by('pk')
    all_machines_dict = {}
    for m in all_machines_qs:
        all_machines_dict[m.pk] = m
    all_machines = list(all_machines_dict.values())

    from datetime import timedelta
    from collections import defaultdict
    today = timezone.now().date().replace(day=1)
    months = [(today - timedelta(days=30 * i)).replace(day=1) for i in reversed(range(6))]
    month_labels = [m.strftime('%b %Y') for m in months]

    start_date = months[0]
    top_machines = (
        TicketSupport.objects.filter(date_creation__date__gte=start_date)
        .values('machine__id', 'machine__nom')
        .annotate(ticket_count=Count('id'))
        .order_by('-ticket_count')[:5]
    )
    machine_ids = [m['machine__id'] for m in top_machines]
    machine_labels = [m['machine__nom'] for m in top_machines]

    from django.db.models.functions import TruncMonth
    data_qs = (
        TicketSupport.objects.filter(
            date_creation__date__gte=start_date,
            machine__id__in=machine_ids
        )
        .annotate(month=TruncMonth('date_creation'))
        .values('machine__id', 'month')
        .annotate(count=Count('id'))
    )

    data_dict = { (item['machine__id'], item['month'].date()): item['count'] for item in data_qs }

    machine_data = []
    for machine_id, label in zip(machine_ids, machine_labels):
        counts = [ data_dict.get((machine_id, m), 0) for m in months ]
        machine_data.append({'label': label, 'data': counts})

    # --- Calculs pour dashboard ---
    # Critiques = tickets ouverts (non terminés/annulés) et priorite haute
    critiques = ticket_base_qs.filter(priorite='haute').exclude(statut__in=['terminee', 'annulee']).count()

    # Temps moyen de résolution (en heures)
    from django.db.models import F, ExpressionWrapper, DurationField
    from django.db.models.functions import Cast
    from django.db import models as dj_models
    resolved_tickets = ticket_base_qs.filter(statut='terminee', date_creation__isnull=False)
    if resolved_tickets.exists() and hasattr(resolved_tickets.first(), 'date_modification'):
        avg_resolution = resolved_tickets.annotate(
            resolution_time=ExpressionWrapper(F('date_modification') - F('date_creation'), output_field=DurationField())
        ).aggregate(avg=dj_models.Avg('resolution_time'))['avg']
        if avg_resolution:
            avg_resolution_hours = round(avg_resolution.total_seconds() / 3600, 1)
        else:
            avg_resolution_hours = None
    else:
        avg_resolution_hours = None

    context = {
        'total_demandes': total_tickets,
        'demandes_en_attente': tickets_en_attente,
        'demandes_en_cours': tickets_en_cours,
        'demandes_terminees': tickets_terminees,
        'demandes_validees': tickets_validees,
        'demandes_annulees': tickets_annulees,
        'demandes_recentes': tickets_recents,
        'stats_machines': stats_machines,
        'total_interventions': total_interventions,
        'interventions_ce_mois': interventions_ce_mois,
        'all_machines': all_machines,
        'month_labels': month_labels,
        'machine_data': machine_data,
        'critiques': critiques,
        'avg_resolution_hours': avg_resolution_hours,
        'opened_pct': opened_pct,
        'resolved_pct': resolved_pct,
        'critiques_diff': critiques_diff,
    }
    return render(request, 'tickets/dashboard.html', context)


@login_required
def machine_list(request):

    user = request.user
    profile = getattr(user, 'operatorprofile', None)
    if is_admin_or_supervisor(user):
        if profile and profile.role == 'superviseur' and profile.department:
            machines_qs = Machine.objects.filter(department=profile.department).annotate(
                nb_demandes=Count('ticketsupport'),
                nb_ouvertes=Count('ticketsupport', filter=Q(ticketsupport__statut__in=['en_attente', 'validee', 'en_cours']))
            ).order_by('nom')
        else:
            machines_qs = Machine.objects.annotate(
                nb_demandes=Count('ticketsupport'),
                nb_ouvertes=Count('ticketsupport', filter=Q(ticketsupport__statut__in=['en_attente', 'validee', 'en_cours']))
            ).order_by('nom')
    else:
        # Opérateur : ne voir que ses machines
        if not profile:
            messages.error(request, "Aucun profil opérateur trouvé.")
            return redirect('dashboard')
        machines_qs = profile.machines.all().annotate(
            nb_demandes=Count('ticketsupport'),
            nb_ouvertes=Count('ticketsupport', filter=Q(ticketsupport__statut__in=['en_attente', 'validee', 'en_cours']))
        ).order_by('nom')

    paginator = Paginator(machines_qs, 24)
    page = request.GET.get('page')
    try:
        machines = paginator.page(page)
    except PageNotAnInteger:
        machines = paginator.page(1)
    except EmptyPage:
        machines = paginator.page(paginator.num_pages)

    return render(request, 'tickets/machine_list.html', {'machines': machines, 'paginator': paginator})


@login_required
def machine_create(request):
    # Restreindre l'accès aux admins et superviseurs
    if not is_admin_or_supervisor(request.user):
        messages.error(request, "Vous n'avez pas la permission de créer une machine.")
        return redirect('dashboard')
    
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
        return redirect('dashboard')
    
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


@login_required
def machine_delete(request, pk):
    """Supprimer une machine (admin uniquement)"""
    # Vérifier que l'utilisateur est un administrateur
    if not request.user.is_superuser:
        messages.error(request, "Seul un administrateur peut supprimer une machine.")
        return redirect('machine_list')
    
    machine = get_object_or_404(Machine, pk=pk)
    
    # Compter les éléments associés (pour information seulement)
    demande_count = TicketSupport.objects.filter(machine=machine).count()
    intervention_count = InterventionTechnique.objects.filter(numero_demande__machine=machine).count()
    
    if request.method == 'POST':
        # Supprimer la machine et tout ce qui est associé (cascade)
        machine.delete()
        messages.success(request, 
            f"Machine '{machine.nom}' supprimée avec succès. "
            f"{demande_count} demande(s) et {intervention_count} intervention(s) ont également été supprimés.")
        return redirect('machine_list')
    
    context = {
        'machine': machine,
        'demande_count': demande_count,
        'intervention_count': intervention_count,
        'admin_mode': True,  # Indiquer qu'on est en mode admin
    }
    return render(request, 'tickets/machine_delete_confirm.html', context)

@login_required
def machine_details(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    return render(request, 'tickets/partials/machine_details_modal.html', {'machine': machine})
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
    from .models import OperatorProfile
    profile, created = OperatorProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
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
    user = request.user
    if is_admin_or_supervisor(user):
        tickets_qs = TicketSupport.objects.all()
    else:
        profile = getattr(user, 'operatorprofile', None)
        if not profile:
            messages.error(request, "Aucun profil opérateur trouvé.")
            return redirect('dashboard')
        tickets_qs = TicketSupport.objects.filter(machine__in=profile.machines.all())

    total = tickets_qs.count()
    en_attente = tickets_qs.filter(statut='en_attente').count()
    validees = tickets_qs.filter(statut='validee').count()
    en_cours = tickets_qs.filter(statut='en_cours').count()
    terminees = tickets_qs.filter(statut='terminee').count()
    annulees = tickets_qs.filter(statut='annulee').count()


    # Recherche par mot-clé
    search_query = request.GET.get('search', '').strip()
    if search_query:
        tickets_qs = tickets_qs.filter(
            Q(numero_ticket__icontains=search_query) |
            Q(titre__icontains=search_query) |
            Q(description_probleme__icontains=search_query) |
            Q(demandeur__icontains=search_query) |
            Q(machine__nom__icontains=search_query)
        )

    # Tickets récents (après filtrage)
    demandes_recentes = tickets_qs.select_related('machine').order_by('-date_creation')[:10]

    # Tickets par service
    stats_services = tickets_qs.values('service_support').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # Tickets par nature de problème
    stats_natures = tickets_qs.values('nature_probleme').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'total': total, 'en_attente': en_attente, 'validees': validees,
        'en_cours': en_cours, 'terminees': terminees, 'annulees': annulees,
        'demandes_recentes': demandes_recentes,
        'stats_services': stats_services,
        'stats_natures': stats_natures,
        'request': request,  # pour pré-remplir la barre de recherche
    }
    return render(request, 'tickets/demande_dashboard.html', context)


@login_required
def demande_list(request):
    """Liste de toutes les demandes d'intervention avec filtres"""
    user = request.user
    if is_admin_or_supervisor(user):
        demandes_qs = TicketSupport.objects.select_related('machine').order_by('-date_creation')
    else:
        # Opérateur : ne voir que les tickets de ses machines
        profile = getattr(user, 'operatorprofile', None)
        if not profile:
            messages.error(request, "Aucun profil opérateur trouvé.")
            return redirect('dashboard')
        demandes_qs = TicketSupport.objects.filter(machine__in=profile.machines.all()).select_related('machine').order_by('-date_creation')
    form = FiltreTicketSupportForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('statut'):
            demandes_qs = demandes_qs.filter(statut=form.cleaned_data['statut'])
        if form.cleaned_data.get('nature_anomalie'):
            demandes_qs = demandes_qs.filter(nature_anomalie=form.cleaned_data['nature_anomalie'])
        if form.cleaned_data.get('service_demandeur'):
            demandes_qs = demandes_qs.filter(service_demandeur__icontains=form.cleaned_data['service_demandeur'])
        if form.cleaned_data.get('machine'):
            try:
                machine = Machine.objects.get(pk=form.cleaned_data['machine'])
                demandes_qs = demandes_qs.filter(machine=machine)
            except Machine.DoesNotExist:
                # Si la machine n'existe pas, ne pas filtrer
                pass
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            demandes_qs = demandes_qs.filter(
                Q(numero_demande__icontains=q) | 
                Q(description_anomalie__icontains=q) | 
                Q(demandeur__icontains=q) |
                Q(machine__nom__icontains=q)
            )
        if form.cleaned_data.get('type_intervention'):
            type_int = form.cleaned_data['type_intervention'] == 'True'
            demandes_qs = demandes_qs.filter(type_intervention=type_int)
    
    # Si requête AJAX pour modal (par machine), renvoyer toutes les demandes correspondantes sans pagination
    if request.GET.get('ajax') == '1':
        context = {'demandes': demandes_qs, 'form': form, 'total': demandes_qs.count()}
        return render(request, 'tickets/partials/tickets_machine_modal.html', context)

    # Pagination pour la liste principale
    paginator = Paginator(demandes_qs, 25)
    page = request.GET.get('page')
    try:
        demandes = paginator.page(page)
    except PageNotAnInteger:
        demandes = paginator.page(1)
    except EmptyPage:
        demandes = paginator.page(paginator.num_pages)

    context = {'demandes': demandes, 'form': form, 'total': demandes_qs.count(), 'paginator': paginator}
    return render(request, 'tickets/demande_list.html', context)


@login_required
def demande_detail(request, pk):
    """Détail d'une demande d'intervention"""
    from .models_ticket_file import TicketSupportFile
    from .models import TicketSupport
    ticket = get_object_or_404(TicketSupport.objects.select_related('machine'), pk=pk)
    fichiers = ticket.fichiers.all()
    context = {'demande': ticket, 'fichiers': fichiers}
    return render(request, 'tickets/demande_detail.html', context)


@login_required
def demande_create(request):
    """Créer une nouvelle demande d'intervention"""
    if request.method == 'POST':
        post_data = request.POST.copy()
        files_data = request.FILES
        # Si la catégorie n'est pas informatique et une machine est sélectionnée, préremplir code_machine
        categorie = post_data.get('categorie')
        machine_id = post_data.get('machine')
        if categorie != 'informatique' and machine_id:
            from .models import Machine
            try:
                machine = Machine.objects.get(pk=machine_id)
                post_data['code_machine'] = machine.reference
            except Machine.DoesNotExist:
                pass
        form = TicketSupportForm(post_data, files_data)
        if form.is_valid():
            demande = form.save(commit=False)
            from django.utils import timezone
            # Remplit automatiquement le nom du demandeur avec l'utilisateur connecté
            if request.user.is_authenticated:
                demande.demandeur = request.user.get_full_name() or request.user.username
            # Remplit date_ticket et heure_ticket si non fournis
            if not demande.date_ticket:
                demande.date_ticket = timezone.now().date()
            if not demande.heure_ticket:
                demande.heure_ticket = timezone.now().time()
            demande.save()
            # Historique création
            from .models import TicketHistory
            TicketHistory.objects.create(
                ticket=demande,
                user=request.user if request.user.is_authenticated else None,
                action="Création du ticket",
                details=f"Ticket créé par {request.user.get_full_name() or request.user.username}",
            )
            # Sauvegarde des fichiers multiples
            fichiers = request.FILES.getlist('fichiers')
            from .models_ticket_file import TicketSupportFile
            for fichier in fichiers:
                TicketSupportFile.objects.create(ticket=demande, fichier=fichier)

            # --- ENVOI EMAIL ALERT élargi ---
            try:
                smtp_settings = SMTPSettings.objects.filter(active=True).first()
                if smtp_settings:
                    from django.contrib.auth.models import User
                    connection = get_connection(
                        host=smtp_settings.host,
                        port=smtp_settings.port,
                        username=smtp_settings.username,
                        password=smtp_settings.password,
                        use_tls=smtp_settings.use_tls,
                        use_ssl=smtp_settings.use_ssl,
                    )
                    recipient_emails = set()
                    # Opérateurs liés à la machine
                    if demande.machine:
                        recipient_emails.update([
                            op.user.email for op in demande.machine.operatorprofile_set.all() if op.user and op.user.email
                        ])
                        # Superviseur du département
                        if demande.machine.department:
                            superviseurs = User.objects.filter(
                                operatorprofile__role='superviseur',
                                operatorprofile__department=demande.machine.department
                            )
                            for sup in superviseurs:
                                if sup.email:
                                    recipient_emails.add(sup.email)
                    # Admins (toujours)
                    admins = User.objects.filter(is_superuser=True)
                    for admin in admins:
                        if admin.email:
                            recipient_emails.add(admin.email)
                    recipient_list = list(recipient_emails)
                    if recipient_list:
                        subject = f"Nouvelle demande de ticket pour la machine {demande.machine.nom if demande.machine else ''}"
                        message = (
                            f"Bonjour,\n\n"
                            f"Un nouveau ticket a été créé concernant la machine : {demande.machine.nom if demande.machine else 'N/A'}.\n\n"
                            f"Détails du ticket :\n"
                            f"- Sujet : {demande.titre}\n"
                            f"- Description : {demande.description_probleme}\n"
                            f"- Créé le : {demande.date_creation.strftime('%d/%m/%Y %H:%M')}\n\n"
                            f"Merci de consulter la plateforme pour plus d'informations.\n\n"
                            f"Cordialement,\nL'équipe support"
                        )
                        email = EmailMessage(
                            subject=subject,
                            body=message,
                            from_email=smtp_settings.from_email,
                            to=recipient_list,
                            connection=connection
                        )
                        email.send(fail_silently=False)
            except Exception as e:
                # Log ou ignorer l'erreur d'envoi d'email
                pass

            messages.success(request, f"Demande '{demande.numero_ticket}' créée avec succès!")
            return redirect('demande_detail', pk=demande.pk)
    else:
        form = TicketSupportForm()
    
    return render(request, 'tickets/demande_form.html', {'form': form, 'action': 'Créer'})


@login_required
def demande_edit(request, pk):
    """Modifier une demande d'intervention"""
    from .models import TicketSupport
    demande = get_object_or_404(TicketSupport, pk=pk)
    
    if request.method == 'POST':
        form = TicketSupportForm(request.POST, request.FILES, instance=demande)
        if form.is_valid():
            # DEBUG : Afficher tous les champs du modèle avant modification
            all_fields = [f.name for f in demande._meta.get_fields() if hasattr(demande, f.name) and not f.many_to_many and not f.one_to_many]
            old_data = {field: getattr(demande, field, None) for field in all_fields}
            if form.cleaned_data.get('fichier'):
                demande.fichier = form.cleaned_data['fichier']
            form.save()
            # DEBUG : Afficher tous les champs du modèle après modification
            new_data = {field: getattr(demande, field, None) for field in all_fields}
            # Champs à ignorer dans l'historique
            ignore_fields = ['code_machine', 'date_modification', 'date_creation', 'id']
            changed_fields = []
            details_list = []
            for field in all_fields:
                if field in ignore_fields:
                    continue
                old = old_data[field]
                new = new_data[field]
                if old != new:
                    changed_fields.append(field)
                    details_list.append(f"{field} (avant : {old}, après : {new})")
            if changed_fields:
                from .models import TicketHistory
                details = "Champs modifiés : " + ", ".join(details_list)
                TicketHistory.objects.create(
                    ticket=demande,
                    user=request.user if request.user.is_authenticated else None,
                    action="Modification du ticket",
                    details=details,
                )
            messages.success(request, f"Demande '{demande.numero_ticket}' mise à jour.")
            return redirect('demande_detail', pk=demande.pk)
    else:
        form = TicketSupportForm(instance=demande)
    
    return render(request, 'tickets/demande_form.html', {'form': form, 'demande': demande, 'action': 'Modifier'})


@login_required
def demande_change_statut(request, pk, statut):
    """Changer le statut d'une demande d'intervention"""
    demande = get_object_or_404(TicketSupport, pk=pk)
    statuts_valides = [s[0] for s in TicketSupport.STATUT_CHOICES]
    if statut in statuts_valides:
        ancien_statut = demande.get_statut_display()
        demande.statut = statut
        demande.save()
        # Historique du changement de statut
        from .models import TicketHistory
        TicketHistory.objects.create(
            ticket=demande,
            user=request.user if request.user.is_authenticated else None,
            action="Changement de statut",
            details=f"Statut changé de '{ancien_statut}' à '{demande.get_statut_display()}' par {request.user.get_full_name() or request.user.username}",
        )
        messages.success(request, f"Statut changé en '{demande.get_statut_display()}'")
    return redirect('demande_detail', pk=pk)


# ============ Vues pour les Interventions Techniques ============

@login_required


@login_required
def viee_dashboard(request):
    """Dashboard pour le suivi de vie des équipements"""
    from django.db.models import Count, Q
    

    user = request.user
    profile = getattr(user, 'operatorprofile', None)
    if is_admin_or_supervisor(user):
        if profile and profile.role == 'superviseur' and profile.department:
            machine_base_qs = Machine.objects.filter(department=profile.department)
        else:
            machine_base_qs = Machine.objects.all()
    else:
        if not profile:
            messages.error(request, "Aucun profil opérateur trouvé.")
            return redirect('dashboard')
        # Show only machines explicitly associated to the operator
        machine_base_qs = profile.machines.all()

    machines_qs = machine_base_qs.annotate(
        nb_demandes=Count('ticketsupport'),
        nb_demandes_ouvertes=Count('ticketsupport', filter=Q(ticketsupport__statut__in=['en_attente', 'validee', 'en_cours'])),
        nb_demandes_critiques=Count('ticketsupport', filter=Q(ticketsupport__nature_probleme='critique', ticketsupport__statut__in=['en_attente', 'validee', 'en_cours'])),
    ).order_by('nom')

    # Pagination pour éviter de charger trop d'objets en mémoire
    paginator = Paginator(machines_qs, 25)  # 25 machines par page
    page = request.GET.get('page')
    try:
        machines = paginator.page(page)
    except PageNotAnInteger:
        machines = paginator.page(1)
    except EmptyPage:
        machines = paginator.page(paginator.num_pages)

    # Calculer le taux de disponibilité pour chaque machine
    for machine in machines:
        # Calculer le temps d'arrêt total en parcourant les interventions
        total_arret_heures = 0
        interventions = InterventionTechnique.objects.filter(
            numero_ticket__machine=machine,
            date_fin_intervention__isnull=False
        )
        
        # Debug: compter les interventions
        nb_interventions_terminees = interventions.count()
        
        for intervention in interventions:
            if intervention.date_fin_intervention and intervention.heure_fin_intervention:
                # Créer les datetime complets
                debut = datetime.datetime.combine(
                    intervention.date_prise_en_compte, 
                    intervention.heure_prise_en_compte
                )
                fin = datetime.datetime.combine(
                    intervention.date_fin_intervention, 
                    intervention.heure_fin_intervention
                )
                # Calculer la durée en heures
                duree = fin - debut
                total_arret_heures += duree.total_seconds() / 3600
        
        # Temps total depuis l'installation (en heures)
        if machine.date_installation:
            temps_total = (timezone.now().date() - machine.date_installation).days * 24
        else:
            # Si pas de date d'installation, utiliser 30 jours par défaut
            temps_total = 30 * 24
        
        # Calcul du taux de disponibilité
        if temps_total > 0:
            temps_disponible = max(0, temps_total - total_arret_heures)
            machine.taux_disponibilite = (temps_disponible / temps_total) * 100
        else:
            machine.taux_disponibilite = 100.0
        
        # Arrondir à 2 décimales
        machine.taux_disponibilite = round(machine.taux_disponibilite, 2)
        
        # Debug info (peut être retiré plus tard)
        machine.debug_info = f"Arret: {total_arret_heures:.1f}h, Total: {temps_total}h, Interventions: {nb_interventions_terminees}"

    # Récupérer les demandes et interventions récentes (limitées)
    demandes_recentes = TicketSupport.objects.select_related('machine').order_by('-date_creation')[:10]
    interventions_recentes = InterventionTechnique.objects.select_related('numero_demande', 'numero_demande__machine').order_by('-date_creation')[:10]
    
    context = {
        'machines': machines,
        'demandes_recentes': demandes_recentes,
        'interventions_recentes': interventions_recentes,
        'paginator': paginator,
    }
    return render(request, 'tickets/viee_dashboard.html', context)


@login_required
def intervention_list(request):
    """Liste de toutes les interventions techniques avec filtres"""
    interventions_qs = InterventionTechnique.objects.select_related(
        'numero_ticket', 'numero_ticket__machine'
    ).order_by('-date_creation')
    form = FiltreTicketSupportForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('type_technicien'):
            interventions_qs = interventions_qs.filter(type_technicien=form.cleaned_data['type_technicien'])
        if form.cleaned_data.get('numero_ticket'):
            interventions_qs = interventions_qs.filter(
                numero_ticket__numero_ticket__icontains=form.cleaned_data['numero_ticket']
            )
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            interventions_qs = interventions_qs.filter(
                Q(description_intervention__icontains=q) | 
                Q(nom_technicien__icontains=q) | 
                Q(nom_prestataire__icontains=q) |
                Q(numero_ticket__machine__nom__icontains=q)
            )
        if form.cleaned_data.get('date_debut'):
            interventions_qs = interventions_qs.filter(
                date_prise_en_compte__gte=form.cleaned_data['date_debut']
            )
        if form.cleaned_data.get('date_fin'):
            interventions_qs = interventions_qs.filter(
                date_prise_en_compte__lte=form.cleaned_data['date_fin']
            )
    paginator = Paginator(interventions_qs, 25)
    page = request.GET.get('page')
    try:
        interventions = paginator.page(page)
    except PageNotAnInteger:
        interventions = paginator.page(1)
    except EmptyPage:
        interventions = paginator.page(paginator.num_pages)
    context = {'interventions': interventions, 'form': form, 'total': interventions_qs.count(), 'paginator': paginator}
    return render(request, 'tickets/intervention_list.html', context)


@login_required
def intervention_detail(request, pk):
    """Détail d'une intervention technique"""
    intervention = get_object_or_404(
        InterventionTechnique.objects.select_related('numero_ticket', 'numero_ticket__machine'), 
        pk=pk
    )
    context = {'intervention': intervention}
    return render(request, 'tickets/intervention_detail.html', context)


@login_required
def intervention_create(request):
    """Créer une nouvelle intervention technique"""
    from .forms import InterventionTechniqueForm
    form = InterventionTechniqueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        intervention = form.save()
        messages.success(request, f"Intervention pour '{intervention.numero_ticket.numero_ticket}' créée avec succès!")
        return redirect('intervention_detail', pk=intervention.pk)
    return render(request, 'tickets/intervention_form.html', {'form': form, 'action': 'Créer'})


@login_required
def intervention_edit(request, pk):
    """Modifier une intervention technique"""
    from .forms import InterventionTechniqueForm
    intervention = get_object_or_404(InterventionTechnique, pk=pk)
    form = InterventionTechniqueForm(request.POST or None, instance=intervention)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Intervention pour '{intervention.numero_ticket.numero_ticket}' mise à jour.")
        return redirect('intervention_detail', pk=intervention.pk)
    return render(request, 'tickets/intervention_form.html', {'form': form, 'intervention': intervention, 'action': 'Modifier'})


@login_required
def intervention_create_from_ticket(request, ticket_pk):
    """Créer une intervention technique à partir d'un ticket"""
    from .forms import InterventionTechniqueForm
    ticket = get_object_or_404(TicketSupport, pk=ticket_pk)
    form = InterventionTechniqueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        intervention = form.save(commit=False)
        intervention.numero_ticket = ticket
        intervention.save()
        messages.success(request, f"Intervention pour '{ticket.numero_ticket}' créée avec succès!")
        return redirect('intervention_detail', pk=intervention.pk)
    return render(request, 'tickets/intervention_form.html', {'form': form, 'action': 'Créer', 'ticket': ticket})

from django.views.decorators.http import require_GET

@require_GET
@login_required
def get_operators_by_department(request):
    department_id = request.GET.get('department_id')
    operators = []
    if department_id:
        operators = OperatorProfile.objects.filter(department_id=department_id)
    data = [
        {'id': op.id, 'name': str(op)} for op in operators
    ]
    return JsonResponse({'operators': data})

