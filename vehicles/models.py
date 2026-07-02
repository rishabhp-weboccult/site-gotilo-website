from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Site(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    present_users = models.ManyToManyField(User, blank=True, related_name='present_at_sites')

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('reachstacker', 'Reachstacker'),
        ('side_shifter', 'Side Shifter'),
        ('forklift', 'Forklift'),
    ]
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('break', 'On Break'),
        ('maintenance', 'Under Maintenance'),
    ]
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='vehicles')
    name = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    
    # Fleet & Hardware details
    vehicle_number = models.CharField(max_length=50, blank=True, null=True, help_text="Registration or Fleet Number")
    box_number = models.CharField(max_length=50, blank=True, null=True, help_text="Telemetry Box Number")
    
    # Device details
    device_name = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Main Controller, GPS Unit")
    device_ip = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, blank=True, null=True)
    device_status = models.CharField(max_length=50, blank=True, null=True, default="Active")
    other_info = models.TextField(blank=True, null=True, help_text="Any additional specifications or details")
    
    # Driver & Status details
    driver_name = models.CharField(max_length=100, blank=True, null=True)
    driver_number = models.CharField(max_length=50, blank=True, null=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('site', 'name')

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.name} ({self.site.name})"

class DeviceIssue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('working', 'Working'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='device_issues')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_issues', help_text="Technician assigned to resolve this issue")
    issue_date_time = models.DateTimeField(help_text="Issue date and time")
    problem_details = models.TextField(help_text="Problem details")
    temp_solution_applied = models.BooleanField(default=False, help_text="Temporary solution applied or not")
    permanent_solution_required = models.BooleanField(default=True, help_text="Permanent solution required")
    permanent_solution_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Permanent solution completed or pending status like (in progress, working, on hold etc)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date_time']

    def __str__(self):
        return f"Issue on {self.vehicle.name} at {self.issue_date_time}"

class Camera(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='cameras')
    name = models.CharField(max_length=100, help_text="e.g., Front Cam, Rear Cam, Cabin Cam")
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True)
    port = models.IntegerField(default=80)
    rtsp_url = models.CharField(max_length=250, blank=True, null=True, help_text="rtsp://username:password@ip:port/stream")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address}) on {self.vehicle.name}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('mid_level', 'Sub Admin'),
        ('technician', 'Ground Operations'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='technician')
    assigned_sites = models.ManyToManyField(Site, blank=True, related_name='technicians')
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

# Automatic UserProfile creation and saving on User creation
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)
