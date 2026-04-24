from django.core.management.base import BaseCommand
from tickets.models import Machine, SparePart

class Command(BaseCommand):
    help = 'Injecte des pièces de rechange de test et les associe aux machines.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Injection des pièces de rechange...')
        spare_parts_data = [
            ("Carte mère CNC", "SP-001", "Carte mère pour tour CNC Alpha", 5),
            ("Variateur ABB", "SP-002", "Variateur de vitesse pour fraiseuse Beta-5", 2),
            ("Courroie convoyeur", "SP-003", "Courroie pour convoyeur principal", 10),
            ("Capteur fin de course", "SP-004", "Capteur pour presse hydraulique", 1),
            ("Filtre chiller", "SP-005", "Filtre pour chiller refroidissement", 4),
        ]
        spare_parts_objs = {}
        for nom, ref, desc, qty in spare_parts_data:
            part, _ = SparePart.objects.get_or_create(
                reference=ref,
                defaults={
                    'nom': nom,
                    'description': desc,
                    'quantite': qty,
                    'actif': True
                }
            )
            spare_parts_objs[ref] = part

        machine_part_map = {
            'TRN-001': ['SP-001'],
            'FRS-002': ['SP-002'],
            'CNV-005': ['SP-003'],
            'PRS-006': ['SP-004'],
            'CHI-008': ['SP-005'],
        }
        for machine_ref, part_refs in machine_part_map.items():
            try:
                machine = Machine.objects.get(reference=machine_ref)
                for part_ref in part_refs:
                    part = spare_parts_objs.get(part_ref)
                    if part:
                        part.machines.add(machine)
            except Machine.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Machine {machine_ref} non trouvée."))
        self.stdout.write(self.style.SUCCESS('Injection terminée.'))
