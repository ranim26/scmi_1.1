from django.db import migrations


def map_type_panne(apps, schema_editor):
    Ticket = apps.get_model('tickets', 'Ticket')
    Department = apps.get_model('tickets', 'Department')

    mapping = {
        'mecanique': 'maintenance',
        'electrique': 'maintenance',
        'electronique': 'informatique',
        'pneumatique': 'maintenance',
        'hydraulique': 'maintenance',
        'logiciel': 'informatique',
        'autre': 'engineer',
    }

    # Update tickets
    for old, new in mapping.items():
        Ticket.objects.filter(type_panne=old).update(type_panne=new)

    # Normalize departments' allowed_types to use the new category names
    deps = {
        'informatique': 'informatique',
        'maintenance': 'maintenance',
        'engineer': 'engineer',
    }
    for nom, val in deps.items():
        Department.objects.filter(nom=nom).update(allowed_types=val)


def reverse_map_type_panne(apps, schema_editor):
    # Reverse is best-effort: map back to a representative old value
    Ticket = apps.get_model('tickets', 'Ticket')
    Department = apps.get_model('tickets', 'Department')

    reverse_map = {
        'informatique': 'electronique',
        'maintenance': 'mecanique',
        'engineer': 'autre',
    }

    for new, old in reverse_map.items():
        Ticket.objects.filter(type_panne=new).update(type_panne=old)

    # Restore departments allowed_types to a safe default list (comma separated)
    Department.objects.filter(nom='informatique').update(allowed_types='electronique,logiciel')
    Department.objects.filter(nom='maintenance').update(allowed_types='mecanique,electrique,pneumatique,hydraulique')
    Department.objects.filter(nom='engineer').update(allowed_types='mecanique,electronique,logiciel')


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_merge'),
    ]

    operations = [
        migrations.RunPython(map_type_panne, reverse_map_type_panne),
    ]
