from django.contrib import admin
from .models import Site, Vehicle, Camera, DeviceIssue

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
    list_display = (
        'name', 'vehicle_number', 'box_number', 'vehicle_type', 'site', 
        'driver_name', 'driver_number', 'availability_status', 
        'device_name', 'device_ip', 'device_status'
    )
    list_filter = ('vehicle_type', 'device_status', 'site', 'availability_status')
    search_fields = ('name', 'vehicle_number', 'box_number', 'device_name', 'device_ip', 'driver_name', 'driver_number')
    inlines = [CameraInline]

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle', 'ip_address', 'port')
    list_filter = ('vehicle__site', 'vehicle')
    search_fields = ('name', 'ip_address')

@admin.register(DeviceIssue)
class DeviceIssueAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'issue_date_time', 'temp_solution_applied', 'permanent_solution_required', 'permanent_solution_status')
    list_filter = ('permanent_solution_status', 'temp_solution_applied', 'permanent_solution_required', 'vehicle')
    search_fields = ('problem_details', 'vehicle__name')

from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_locked', 'failed_login_attempts')
    list_filter = ('role', 'is_locked')
    search_fields = ('user__username', 'user__email')

