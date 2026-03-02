from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crée des utilisateurs opérateurs/superviseurs et les assigne aux départements demandés.'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from tickets.models import Department, OperatorProfile

        User = get_user_model()

        # Define users to create/update: (username, first, last, department, role)
        accounts = [
            ('engineer1', 'Ing', 'Op', 'engineer', 'operateur'),
            ('sup_it', 'Sup', 'Informatique', 'informatique', 'superviseur'),
            ('sup_maintenance', 'Sup', 'Maintenance', 'maintenance', 'superviseur'),
            ('sup_engineer', 'Sup', 'Engineer', 'engineer', 'superviseur'),
        ]

        for username, first, last, dept_name, role in accounts:
            user, created = User.objects.get_or_create(username=username,
                                                       defaults={'first_name': first, 'last_name': last, 'email': f'{username}@example.com'})
            if created:
                user.set_password('demo123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Utilisateur créé: {username} (pwd=demo123)'))
            else:
                self.stdout.write(f'Utilisateur existant: {username}, mise à jour du profil')

            try:
                dept = Department.objects.get(nom__iexact=dept_name)
            except Department.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Département introuvable: {dept_name}'))
                continue

            profile = getattr(user, 'operatorprofile', None)
            if not profile:
                profile = OperatorProfile.objects.create(user=user, department=dept, role=role)
            else:
                profile.department = dept
                profile.role = role
                profile.save()

            self.stdout.write(self.style.SUCCESS(f'Assigné {username} -> {dept.nom} ({role})'))
