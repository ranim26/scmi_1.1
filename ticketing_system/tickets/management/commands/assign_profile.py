from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Assigne un Department et un role à un utilisateur (par username ou prénom nom)'

    def add_arguments(self, parser):
        parser.add_argument('user_identifier', type=str, help='username ou "Prénom Nom"')
        parser.add_argument('department', type=str, help='Nom du département (informatique|maintenance|engineer)')
        parser.add_argument('--role', type=str, choices=['operateur', 'superviseur'], default='operateur')

    def handle(self, *args, **options):
        User = get_user_model()
        identifier = options['user_identifier']
        dept_name = options['department']
        role = options['role']

        # lazy import to avoid app registry issues
        from tickets.models import Department

        # find user by username or "First Last"
        user = None
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            parts = identifier.split()
            if len(parts) >= 2:
                first = parts[0]
                last = ' '.join(parts[1:])
                try:
                    user = User.objects.get(first_name=first, last_name=last)
                except User.DoesNotExist:
                    pass

        if not user:
            raise CommandError(f"Utilisateur introuvable: {identifier}")

        try:
            department = Department.objects.get(nom__iexact=dept_name)
        except Department.DoesNotExist:
            raise CommandError(f"Département introuvable: {dept_name}")

        profile = getattr(user, 'operatorprofile', None)
        if not profile:
            # create profile if missing
            from tickets.models import OperatorProfile
            profile = OperatorProfile.objects.create(user=user, department=department, role=role)
        else:
            profile.department = department
            profile.role = role
            profile.save()

        self.stdout.write(self.style.SUCCESS(f"Assigné {user.username} -> {department.nom} ({role})"))
