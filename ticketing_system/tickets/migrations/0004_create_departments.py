from django.db import migrations


def create_departments(apps, schema_editor):
    Department = apps.get_model('tickets', 'Department')
    Department.objects.update_or_create(
        nom='informatique',
        defaults={'allowed_types': 'electronique,logiciel'}
    )
    Department.objects.update_or_create(
        nom='maintenance',
        defaults={'allowed_types': 'mecanique,electrique,pneumatique,hydraulique'}
    )
    Department.objects.update_or_create(
        nom='engineer',
        defaults={'allowed_types': 'mecanique,electronique,logiciel'}
    )


def delete_departments(apps, schema_editor):
    Department = apps.get_model('tickets', 'Department')
    Department.objects.filter(nom__in=['informatique', 'maintenance', 'engineer']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_alter_ticket_machine'),
    ]

    operations = [
        migrations.RunPython(create_departments, delete_departments),
    ]
