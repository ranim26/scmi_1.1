from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Assigne le département 'maintenance' aux superviseurs sans département"

    def handle(self, *args, **options):
        from tickets.models import OperatorProfile, Department

        try:
            dept = Department.objects.get(nom__iexact='maintenance')
        except Department.DoesNotExist:
            self.stdout.write(self.style.ERROR("Département 'maintenance' introuvable."))
            return

        qs = OperatorProfile.objects.filter(role='superviseur', department__isnull=True).select_related('user')
        if not qs.exists():
            self.stdout.write('Aucun superviseur sans département trouvé.')
            return

        for profile in qs:
            profile.department = dept
            profile.save()
            self.stdout.write(self.style.SUCCESS(f"Assigné {profile.user.username} -> maintenance"))
