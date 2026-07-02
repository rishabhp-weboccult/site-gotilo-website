import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gotilo_site.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import UserProfile

def seed():
    # Delete old supperadmin if it exists
    User.objects.filter(username='supperadmin').delete()
    print("Deleted old 'supperadmin' account.")

    # 1. Super Admin: weboccultadmin / 12345678
    sa_user, created = User.objects.get_or_create(username='weboccultadmin', email='superadmin@example.com')
    if created or not sa_user.check_password('12345678'):
        sa_user.set_password('12345678')
        sa_user.is_superuser = True
        sa_user.is_staff = True
        sa_user.save()
    sa_profile, _ = UserProfile.objects.get_or_create(user=sa_user)
    sa_profile.role = 'super_admin'
    sa_profile.save()
    print("Super admin user 'weboccultadmin' seeded.")

    # 2. Mid Level User
    ml_user, created = User.objects.get_or_create(username='miduser', email='miduser@example.com')
    if created or not ml_user.check_password('password123'):
        ml_user.set_password('password123')
        ml_user.save()
    ml_profile, _ = UserProfile.objects.get_or_create(user=ml_user)
    ml_profile.role = 'mid_level'
    ml_profile.save()
    print("Mid-level user 'miduser' seeded.")

    # 3. Technician User
    tech_user, created = User.objects.get_or_create(username='techuser', email='techuser@example.com')
    if created or not tech_user.check_password('password123'):
        tech_user.set_password('password123')
        tech_user.save()
    tech_profile, _ = UserProfile.objects.get_or_create(user=tech_user)
    tech_profile.role = 'technician'
    tech_profile.save()
    print("Technician user 'techuser' seeded.")

if __name__ == '__main__':
    seed()
