from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from .models import Site, Vehicle, Camera

def dashboard(request):
    """
    Landing page that lists all sites and displays overall metrics.
    """
    sites = Site.objects.prefetch_related('vehicles__cameras').all()
    
    # Calculate overall stats
    total_sites = sites.count()
    total_vehicles = Vehicle.objects.count()
    total_cameras = Camera.objects.count()
    
    # Count vehicles by type
    reachstackers = Vehicle.objects.filter(vehicle_type='reachstacker').count()
    side_shifters = Vehicle.objects.filter(vehicle_type='side_shifter').count()
    forklifts = Vehicle.objects.filter(vehicle_type='forklift').count()
    
    context = {
        'sites': sites,
        'total_sites': total_sites,
        'total_vehicles': total_vehicles,
        'total_cameras': total_cameras,
        'reachstackers': reachstackers,
        'side_shifters': side_shifters,
        'forklifts': forklifts,
    }
    return render(request, 'vehicles/dashboard.html', context)

def site_detail(request, site_id):
    """
    Details of a specific site showing all its vehicles and cameras.
    """
    site = get_object_or_404(Site.objects.prefetch_related('vehicles__cameras'), pk=site_id)
    vehicles = site.vehicles.all()
    
    context = {
        'site': site,
        'vehicles': vehicles,
    }
    return render(request, 'vehicles/site_detail.html', context)

def add_site(request):
    """
    View to add a new site.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        description = request.POST.get('description')
        
        if not name:
            messages.error(request, "Site name is required.")
            return redirect('dashboard')
            
        try:
            site = Site.objects.create(name=name, location=location, description=description)
            messages.success(request, f"Site '{site.name}' created successfully.")
            return redirect('site_detail', site_id=site.id)
        except Exception as e:
            messages.error(request, f"Error creating site: {e}")
            return redirect('dashboard')
            
    return redirect('dashboard')

def edit_site(request, site_id):
    """
    View to edit an existing site.
    """
    site = get_object_or_404(Site, pk=site_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        description = request.POST.get('description')
        
        if not name:
            messages.error(request, "Site name is required.")
            return redirect('site_detail', site_id=site.id)
            
        try:
            site.name = name
            site.location = location
            site.description = description
            site.save()
            messages.success(request, f"Site '{site.name}' updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating site: {e}")
            
    return redirect('site_detail', site_id=site.id)

def delete_site(request, site_id):
    """
    View to delete a site.
    """
    site = get_object_or_404(Site, pk=site_id)
    if request.method == 'POST':
        site_name = site.name
        site.delete()
        messages.success(request, f"Site '{site_name}' has been deleted.")
        return redirect('dashboard')
    return redirect('site_detail', site_id=site.id)

def add_vehicle(request, site_id):
    """
    Add a new vehicle to a site, along with its details and cameras.
    """
    site = get_object_or_404(Site, pk=site_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        vehicle_type = request.POST.get('vehicle_type')
        vehicle_number = request.POST.get('vehicle_number')
        box_number = request.POST.get('box_number')
        device_name = request.POST.get('device_name')
        device_ip = request.POST.get('device_ip') or None
        device_status = request.POST.get('device_status') or 'Active'
        other_info = request.POST.get('other_info')
        
        if not name or not vehicle_type:
            messages.error(request, "Vehicle name and type are required.")
            return render(request, 'vehicles/vehicle_form.html', {'site': site, 'vehicle_types': Vehicle.VEHICLE_TYPES})
            
        try:
            with transaction.atomic():
                # Create the vehicle
                vehicle = Vehicle.objects.create(
                    site=site,
                    name=name,
                    vehicle_type=vehicle_type,
                    vehicle_number=vehicle_number,
                    box_number=box_number,
                    device_name=device_name,
                    device_ip=device_ip,
                    device_status=device_status,
                    other_info=other_info
                )
                
                # Retrieve camera lists from form
                cam_names = request.POST.getlist('camera_name[]')
                cam_ips = request.POST.getlist('camera_ip[]')
                cam_ports = request.POST.getlist('camera_port[]')
                cam_rtsps = request.POST.getlist('camera_rtsp[]')
                
                for i in range(len(cam_names)):
                    name_val = cam_names[i].strip()
                    ip_val = cam_ips[i].strip()
                    
                    if name_val and ip_val:
                        port_val = int(cam_ports[i].strip()) if cam_ports[i].strip().isdigit() else 80
                        rtsp_val = cam_rtsps[i].strip()
                        
                        Camera.objects.create(
                            vehicle=vehicle,
                            name=name_val,
                            ip_address=ip_val,
                            port=port_val,
                            rtsp_url=rtsp_val
                        )
                
                messages.success(request, f"Vehicle '{vehicle.name}' added successfully to site '{site.name}'.")
                return redirect('site_detail', site_id=site.id)
                
        except Exception as e:
            messages.error(request, f"Error saving vehicle: {e}")
            
    # GET request
    context = {
        'site': site,
        'vehicle_types': Vehicle.VEHICLE_TYPES,
        'action': 'Add'
    }
    return render(request, 'vehicles/vehicle_form.html', context)

def edit_vehicle(request, vehicle_id):
    """
    Edit a vehicle's details and cameras.
    """
    vehicle = get_object_or_404(Vehicle.objects.select_related('site').prefetch_related('cameras'), pk=vehicle_id)
    site = vehicle.site
    
    if request.method == 'POST':
        name = request.POST.get('name')
        vehicle_type = request.POST.get('vehicle_type')
        vehicle_number = request.POST.get('vehicle_number')
        box_number = request.POST.get('box_number')
        device_name = request.POST.get('device_name')
        device_ip = request.POST.get('device_ip') or None
        device_status = request.POST.get('device_status') or 'Active'
        other_info = request.POST.get('other_info')
        
        if not name or not vehicle_type:
            messages.error(request, "Vehicle name and type are required.")
            return render(request, 'vehicles/vehicle_form.html', {'site': site, 'vehicle': vehicle, 'vehicle_types': Vehicle.VEHICLE_TYPES, 'action': 'Edit'})
            
        try:
            with transaction.atomic():
                # Update vehicle details
                vehicle.name = name
                vehicle.vehicle_type = vehicle_type
                vehicle.vehicle_number = vehicle_number
                vehicle.box_number = box_number
                vehicle.device_name = device_name
                vehicle.device_ip = device_ip
                vehicle.device_status = device_status
                vehicle.other_info = other_info
                vehicle.save()
                
                # Delete existing cameras and recreate
                vehicle.cameras.all().delete()
                
                cam_names = request.POST.getlist('camera_name[]')
                cam_ips = request.POST.getlist('camera_ip[]')
                cam_ports = request.POST.getlist('camera_port[]')
                cam_rtsps = request.POST.getlist('camera_rtsp[]')
                
                for i in range(len(cam_names)):
                    name_val = cam_names[i].strip()
                    ip_val = cam_ips[i].strip()
                    
                    if name_val and ip_val:
                        port_val = int(cam_ports[i].strip()) if cam_ports[i].strip().isdigit() else 80
                        rtsp_val = cam_rtsps[i].strip()
                        
                        Camera.objects.create(
                            vehicle=vehicle,
                            name=name_val,
                            ip_address=ip_val,
                            port=port_val,
                            rtsp_url=rtsp_val
                        )
                        
                messages.success(request, f"Vehicle '{vehicle.name}' updated successfully.")
                return redirect('site_detail', site_id=site.id)
                
        except Exception as e:
            messages.error(request, f"Error saving vehicle: {e}")
            
    # GET request
    context = {
        'site': site,
        'vehicle': vehicle,
        'vehicle_types': Vehicle.VEHICLE_TYPES,
        'cameras': vehicle.cameras.all(),
        'action': 'Edit'
    }
    return render(request, 'vehicles/vehicle_form.html', context)

def delete_vehicle(request, vehicle_id):
    """
    Delete a vehicle.
    """
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    site_id = vehicle.site.id
    if request.method == 'POST':
        veh_name = vehicle.name
        vehicle.delete()
        messages.success(request, f"Vehicle '{veh_name}' has been deleted.")
    return redirect('site_detail', site_id=site_id)
