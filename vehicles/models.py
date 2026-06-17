from django.db import models

class Site(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('reachstacker', 'Reachstacker'),
        ('side_shifter', 'Side Shifter'),
        ('forklift', 'Forklift'),
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
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('site', 'name')

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.name} ({self.site.name})"

class Camera(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='cameras')
    name = models.CharField(max_length=100, help_text="e.g., Front Cam, Rear Cam, Cabin Cam")
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True)
    port = models.IntegerField(default=80)
    rtsp_url = models.CharField(max_length=250, blank=True, null=True, help_text="rtsp://username:password@ip:port/stream")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address}) on {self.vehicle.name}"
