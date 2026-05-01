from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import TicketSupport
from tickets.models_smtp import SMTPSettings
from django.core.mail import send_mail, get_connection, EmailMessage
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Check SLA status for tickets and send alerts for overdue or warning tickets.'

    def handle(self, *args, **options):
        now = timezone.now().date()
        # Recalculate SLA status for all tickets
        for ticket in TicketSupport.objects.all():
            ticket.update_sla_status()
            ticket.save(update_fields=['sla_status'])

        overdue_tickets = TicketSupport.objects.filter(sla_status='overdue')
        warning_tickets = TicketSupport.objects.filter(sla_status='warning')

        # Get all supervisors and admins
        supervisors = User.objects.filter(operatorprofile__role='superviseur')
        admins = User.objects.filter(is_superuser=True)
        recipients = set()
        for user in supervisors.union(admins):
            if user.email:
                recipients.add(user.email)
        recipients = list(recipients)

        smtp_settings = SMTPSettings.objects.filter(active=True).first()
        if not smtp_settings or not recipients:
            self.stdout.write(self.style.WARNING('No SMTP settings or recipients found.'))
            return

        connection = get_connection(
            host=smtp_settings.host,
            port=smtp_settings.port,
            username=smtp_settings.username,
            password=smtp_settings.password,
            use_tls=smtp_settings.use_tls,
            use_ssl=smtp_settings.use_ssl,
        )

        # Send emails for overdue tickets
        for ticket in overdue_tickets:
            subject = f"[SLA] Ticket en retard: {ticket.numero_ticket}"
            message = f"Le ticket {ticket.numero_ticket} est en retard (SLA dépassé).\nMachine: {ticket.machine.nom}\nDemandeur: {ticket.demandeur}\nDescription: {ticket.description_probleme}"
            email = EmailMessage(subject, message, smtp_settings.from_email, recipients, connection=connection)
            email.send(fail_silently=True)
            self.stdout.write(self.style.SUCCESS(f"Alert sent for overdue ticket {ticket.numero_ticket}"))

        # Send emails for warning tickets
        for ticket in warning_tickets:
            subject = f"[SLA] Ticket bientôt en retard: {ticket.numero_ticket}"
            message = f"Le ticket {ticket.numero_ticket} approche de la date limite SLA.\nMachine: {ticket.machine.nom}\nDemandeur: {ticket.demandeur}\nDescription: {ticket.description_probleme}"
            email = EmailMessage(subject, message, smtp_settings.from_email, recipients, connection=connection)
            email.send(fail_silently=True)
            self.stdout.write(self.style.SUCCESS(f"Alert sent for warning ticket {ticket.numero_ticket}"))

        self.stdout.write(self.style.SUCCESS('SLA alert check completed.'))
