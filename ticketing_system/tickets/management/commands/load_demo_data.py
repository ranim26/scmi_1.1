from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import Machine, Department, InterventionTechnique
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Charge des données de démonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write('Création des données de démonstration...')

        # Créer des utilisateurs techniciens
        techniciens = []
        for username, first, last in [
            ('tech1', 'Ahmed', 'Benali'),
            ('tech2', 'Mohamed', 'Chaouche'),
            ('superviseur', 'Karim', 'Mansouri'),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first, 'last_name': last, 'email': f'{username}@industrie.com'}
            )
            if created:
                user.set_password('demo123')
                user.save()
            techniciens.append(user)

        # Créer un utilisateur IT
        it_user, created = User.objects.get_or_create(
            username='it1',
            defaults={'first_name': 'Nabil', 'last_name': 'Kacem', 'email': 'it1@industrie.com'}
        )
        if created:
            it_user.set_password('demo123')
            it_user.save()

        # Créer l'admin si nécessaire
        admin, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={'first_name': 'Admin', 'last_name': 'User', 'email': 'admin@industrie.com', 'is_staff': True, 'is_superuser': True}
        )
        if created_admin:
            admin.set_password('admin123')
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        # Créer des machines
        machines_data = [
            ('Tour CNC Alpha', 'TRN-001', 'Atelier A - Zone 1', 'Tour à commande numérique pour pièces mécaniques'),
            ('Fraiseuse Beta-5', 'FRS-002', 'Atelier A - Zone 2', 'Fraiseuse 5 axes haute précision'),
            ('Compresseur Principal', 'CMP-003', 'Salle technique', 'Compresseur air 10 bars alimentation générale'),
            ('Robot Soudage R1', 'ROB-004', 'Atelier B - Zone 3', 'Robot de soudage automatique MIG/MAG'),
            ('Convoyeur Principal', 'CNV-005', 'Ligne de production', 'Convoyeur à bandes 50m'),
            ('Presse Hydraulique 200T', 'PRS-006', 'Atelier C', 'Presse hydraulique 200 tonnes'),
            ('Générateur Backup', 'GEN-007', 'Salle électrique', 'Groupe électrogène 500 KVA'),
            ('Chiller Refroidissement', 'CHI-008', 'Toit', 'Refroidisseur industriel process'),
        ]

        machines = []
        for nom, ref, loc, desc in machines_data:
            machine, _ = Machine.objects.get_or_create(
                reference=ref,
                defaults={'nom': nom, 'localisation': loc, 'description': desc}
            )
            machines.append(machine)

        admin = User.objects.filter(username='admin').first()

        # Créer des demandes de démonstration (adapté au modèle `InterventionTechnique`)
        tickets_data = [
            ('Vibrations anormales - tour CNC Alpha', machines[0], 'mecanique', 'critique', 'ouvert',
             'La machine émet des vibrations importantes lors du tournage. Production arrêtée.'),
            ('Erreur variateur vitesse fraiseuse', machines[1], 'electrique', 'haute', 'en_cours',
             'Erreur E03 sur variateur ABB. La fraiseuse s\'arrête aléatoirement.'),
            ('Fuite d\'huile compresseur', machines[2], 'mecanique', 'moyenne', 'ouvert',
             'Fuite d\'huile constatée au niveau du joint d\'arbre. Consommation anormale.'),
            ('Robot soudage - perte position Home', machines[3], 'electronique', 'critique', 'en_cours',
             'Le robot perd sa position de référence. Calibration impossible. Production bloquée.'),
            ('Convoyeur - courroie usée', machines[4], 'mecanique', 'basse', 'en_attente',
             'Courroie centrale montrant des signes d\'usure. Remplacement préventif recommandé.'),
            ('Presse - défaut capteur fin de course', machines[5], 'electronique', 'haute', 'ouvert',
             'Capteur fin de course ne répond plus. Sécurité machine déclenchée.'),
            ('Onduleur salle informatique alarme', machines[6], 'electrique', 'moyenne', 'resolu',
             'Alarme batterie faible onduleur. Batteries changées, problème résolu.'),
            ('Chiller - temperature process élevée', machines[7], 'mecanique', 'haute', 'en_cours',
             'Température de sortie process 5°C au-dessus consigne. Filtre à nettoyer.'),
        ]

        # statut_map pour correspondre aux choix de `InterventionTechnique`
        statut_map = {
            'ouvert': 'en_attente',
            'en_attente': 'en_attente',
            'en_cours': 'en_cours',
            'resolu': 'terminee',
            'ferme': 'terminee',
        }

        from tickets.models import TicketSupport
        for titre, machine, type_p, prio, statut, desc in tickets_data:
            statut_mapped = statut_map.get(statut, 'en_attente')
            # éviter doublons par titre
            if not TicketSupport.objects.filter(titre=titre).exists():
                ticket = TicketSupport.objects.create(
                    titre=titre,
                    categorie='industrielle',
                    type_panne=type_p,
                    priorite='moyenne',  # adapt as needed
                    statut=statut_mapped,
                    description_probleme=desc,
                    service_support='Maintenance',
                    demandeur=(admin.username if admin else 'system'),
                    machine=machine,
                    code_machine=machine.reference,
                    date_ticket=timezone.now().date(),
                    heure_ticket=timezone.now().time(),
                    nature_probleme=type_p if type_p in dict(TicketSupport.NATURE_ANOMALIE_CHOICES) else 'autre',
                )
                # Now create the intervention linked to this ticket
                InterventionTechnique.objects.create(
                    nom_technicien=titre,
                    type_technicien='interne',
                    description_intervention=desc,
                    numero_ticket=ticket,
                    date_prise_en_compte=timezone.now().date(),
                    heure_prise_en_compte=timezone.now().time(),
                )

        # Assigner les profils aux départements
        dep_informatique = Department.objects.filter(nom='informatique').first()
        dep_maintenance = Department.objects.filter(nom='maintenance').first()
        dep_engineer = Department.objects.filter(nom='engineer').first()

        # Assigner department et role via OperatorProfile (créé automatiquement si absent)
        def assign_profile(user, department, role='operateur'):
            profile = getattr(user, 'operatorprofile', None)
            if profile:
                profile.department = department
                profile.role = role
                profile.save()

        assign_profile(techniciens[0], dep_maintenance, 'operateur')
        assign_profile(techniciens[1], dep_engineer, 'operateur')
        assign_profile(it_user, dep_informatique, 'operateur')
        assign_profile(techniciens[2], dep_maintenance, 'superviseur')

        from tickets.models import TicketSupport
        self.stdout.write(self.style.SUCCESS(
            f'✅ Données créées: {Machine.objects.count()} machines, {TicketSupport.objects.count()} tickets\n'
            f'   Comptes: admin/admin123 | tech1/demo123 | tech2/demo123 | it1/demo123 | superviseur/demo123'
        ))
