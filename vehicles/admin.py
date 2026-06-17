from django.contrib import admin
from .models import Site, Vehicle, Camera

class CameraInline(admin.TabularInline):
    model = Camera
    extra = 1

class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 1

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_at')
    search_fields = ('name', 'location')
    inlines = [VehicleInline]

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_number', 'box_number', 'vehicle_type', 'site', 'device_name', 'device_ip', 'device_status')
    list_filter = ('vehicle_type', 'device_status', 'site')
    search_fields = ('name', 'vehicle_number', 'box_number', 'device_name', 'device_ip')
    inlines = [CameraInline]

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle', 'ip_address', 'port')
    list_filter = ('vehicle__site', 'vehicle')
    search_fields = ('name', 'ip_address')
