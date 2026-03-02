from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Assigne automatiquement les départements aux OperatorProfile selon des règles de username.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Appliquer les changements (par défaut affiche le plan)')

    def handle(self, *args, **options):
        from tickets.models import OperatorProfile, Department

        profiles = OperatorProfile.objects.select_related('user', 'department').all()
        plan = []
        for p in profiles:
            username = p.user.username.lower()
            target = None
            if 'tech' in username or 'super' in username or 'sup' in username:
                target = 'maintenance'
            elif 'it' in username or 'admin' in username:
                target = 'informatique'
            elif 'eng' in username or 'engineer' in username:
                target = 'engineer'

            if target:
                plan.append((p.user.username, p.department.nom if p.department else None, target))

        if not plan:
            self.stdout.write('Aucun profil correspondant aux règles automatiques trouvé.')
            return

        self.stdout.write('Plan d\'assignation (username | actuel -> cible):')
        for u, cur, tgt in plan:
            self.stdout.write(f' - {u} | {cur} -> {tgt}')

        if not options['apply']:
            self.stdout.write('\nExécutez avec --apply pour appliquer ces changements.')
            return

        # Apply
        for u, cur, tgt in plan:
            p = OperatorProfile.objects.get(user__username=u)
            try:
                dept = Department.objects.get(nom__iexact=tgt)
            except Department.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Département introuvable: {tgt}'))
                continue
            p.department = dept
            p.save()
            self.stdout.write(self.style.SUCCESS(f'Assigné {u} -> {tgt}'))
