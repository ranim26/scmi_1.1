from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Machines
    path('machines/<int:pk>/details/', views.machine_details, name='machine_details'),
    path('machines/', views.machine_list, name='machine_list'),
    path('machines/nouvelle/', views.machine_create, name='machine_create'),
    path('machines/<int:pk>/modifier/', views.machine_edit, name='machine_edit'),
    path('machines/<int:pk>/supprimer/', views.machine_delete, name='machine_delete'),
    path('machines/<int:pk>/activer/', views.activate_machine, name='machine_activate'),
    path('machines/<int:pk>/desactiver/', views.deactivate_machine, name='machine_deactivate'),
    path('profil/machines/', views.choisir_machines, name='choisir_machines'),
    # Gestion des utilisateurs (Admin uniquement)
    path('utilisateurs/', views.user_list, name='user_list'),
    path('utilisateurs/nouveau/', views.user_create, name='user_create'),
    path('utilisateurs/<int:pk>/modifier/', views.user_edit, name='user_edit'),
    path('utilisateurs/<int:pk>/supprimer/', views.user_delete, name='user_delete'),
    # Demandes d'intervention
    path('demandes/', views.demande_list, name='demande_list'),
    path('demandes/dashboard/', views.demande_dashboard, name='demande_dashboard'),
    path('demandes/nouvelle/', views.demande_create, name='demande_create'),
    path('demandes/<int:pk>/', views.demande_detail, name='demande_detail'),
    path('demandes/<int:pk>/modifier/', views.demande_edit, name='demande_edit'),
    path('demandes/<int:pk>/statut/<str:statut>/', views.demande_change_statut, name='demande_change_statut'),
    # Interventions techniques
    path('interventions/', views.intervention_list, name='intervention_list'),
    path('interventions/viee/', views.viee_dashboard, name='viee_dashboard'),
    path('interventions/nouvelle/', views.intervention_create, name='intervention_create'),
    path('interventions/<int:pk>/', views.intervention_detail, name='intervention_detail'),
    path('interventions/<int:pk>/modifier/', views.intervention_edit, name='intervention_edit'),
    path('interventions/from-ticket/<int:ticket_pk>/', views.intervention_create_from_ticket, name='intervention_create_from_ticket'),
    # AJAX endpoint for operator filtering by department
    path('ajax/get-operators/', views.get_operators_by_department, name='get_operators_by_department'),
]
