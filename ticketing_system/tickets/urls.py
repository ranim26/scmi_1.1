from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/nouveau/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/modifier/', views.ticket_edit, name='ticket_edit'),
    path('tickets/<int:pk>/statut/<str:statut>/', views.ticket_change_statut, name='ticket_change_statut'),
    path('machines/', views.machine_list, name='machine_list'),
    path('machines/nouvelle/', views.machine_create, name='machine_create'),
    path('machines/<int:pk>/modifier/', views.machine_edit, name='machine_edit'),
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
    path('interventions/dashboard/', views.intervention_dashboard, name='intervention_dashboard'),
    path('interventions/viee/', views.viee_dashboard, name='viee_dashboard'),
    path('interventions/nouvelle/', views.intervention_create, name='intervention_create'),
    path('interventions/<int:pk>/', views.intervention_detail, name='intervention_detail'),
    path('interventions/<int:pk>/modifier/', views.intervention_edit, name='intervention_edit'),
    path('interventions/from-demande/<int:demande_pk>/', views.intervention_create_from_demande, name='intervention_create_from_demande'),
]
