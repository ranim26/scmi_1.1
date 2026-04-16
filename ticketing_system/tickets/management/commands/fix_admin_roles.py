from django.contrib.auth.models import User
from tickets.models import OperatorProfile

def run():
    users = User.objects.all()
    for user in users:
        profile = getattr(user, 'operatorprofile', None)
        if user.is_superuser and user.is_staff:
            if profile and profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
                print(f"Profil de {user.username} mis à jour en 'admin'.")
            elif not profile:
                OperatorProfile.objects.create(user=user, role='admin')
                print(f"Profil créé pour {user.username} avec rôle 'admin'.")
        else:
            # Optionnel : rétrograder les anciens admins qui ne sont plus superuser/staff
            if profile and profile.role == 'admin':
                profile.role = 'operateur'
                profile.save()
                print(f"Profil de {user.username} rétrogradé en 'operateur'.")
    print("Mise à jour terminée.")
