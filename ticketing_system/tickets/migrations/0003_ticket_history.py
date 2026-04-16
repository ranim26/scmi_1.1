from django.db import migrations, models
import django.utils.timezone
import django.conf

class Migration(migrations.Migration):
    dependencies = [
        ('tickets', '0002_alter_operatorprofile_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('ticket', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='histories', to='tickets.ticketsupport')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
