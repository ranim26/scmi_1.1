from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Liste tous les OperatorProfile avec username, role et department'

    def handle(self, *args, **options):
        from tickets.models import OperatorProfile

        qs = OperatorProfile.objects.select_related('user', 'department').all()
        if not qs.exists():
            self.stdout.write('Aucun OperatorProfile trouvé.')
            return

        self.stdout.write(f"{'username':<20} {'role':<12} {'department':<15}")
        self.stdout.write('-' * 50)
        for p in qs:
            dept = p.department.nom if p.department else 'None'
            self.stdout.write(f"{p.user.username:<20} {p.role:<12} {dept:<15}")
