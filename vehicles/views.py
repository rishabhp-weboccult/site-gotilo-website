from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Site, Vehicle, Camera, DeviceIssue, UserProfile
from django.utils import timezone

# ----------------- AUTHENTICATION VIEWS -----------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if user exists and is locked out
        try:
            temp_user = User.objects.get(username=username)
            if temp_user.profile.is_locked:
                messages.error(request, "This account has been locked due to too many failed login attempts. Please contact a Super Admin.")
                return render(request, 'vehicles/login.html', {'next': next_url})
        except User.DoesNotExist:
            temp_user = None

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Reset failed attempts
            user.profile.failed_login_attempts = 0
            user.profile.is_locked = False
            user.profile.save()
            
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect(next_url)
        else:
            if temp_user is not None:
                temp_user.profile.failed_login_attempts += 1
                if temp_user.profile.failed_login_attempts >= 10:
                    temp_user.profile.is_locked = True
                    temp_user.profile.save()
                    messages.error(request, "This account has been locked due to 10 failed login attempts. Please contact a Super Admin.")
                else:
                    temp_user.profile.save()
                    remaining = 10 - temp_user.profile.failed_login_attempts
                    messages.error(request, f"Invalid password. Account will lock after {remaining} more failed attempts.")
            else:
                messages.error(request, "Invalid username or password.")
            
    return render(request, 'vehicles/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

# ----------------- USER MANAGEMENT (SUPER ADMIN) -----------------

def user_management(request):
    if not request.user.is_authenticated or request.user.profile.role != 'super_admin':
        messages.error(request, "Access restricted to Super Admins.")
        return redirect('dashboard')
        
    users = User.objects.select_related('profile').all().order_by('username')
    sites = Site.objects.all().order_by('name')
    context = {
        'users': users,
        'sites': sites,
    }
    return render(request, 'vehicles/user_management.html', context)

def add_user(request):
    if not request.user.is_authenticated or request.user.profile.role != 'super_admin':
        messages.error(request, "Access restricted to Super Admins.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'technician')
        assigned_sites_ids = request.POST.getlist('assigned_sites[]')
        
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('user_management')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return redirect('user_management')
            
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)
                # Profile is auto-created via signal
                profile = user.profile
                profile.role = role
                if role == 'technician' and assigned_sites_ids:
                    sites = Site.objects.filter(id__in=assigned_sites_ids)
                    profile.assigned_sites.set(sites)
                profile.save()
            messages.success(request, f"User account '{username}' registered successfully.")
        except Exception as e:
            messages.error(request, f"Error registering user: {e}")
            
    return redirect('user_management')

def delete_user(request, user_id):
    if not request.user.is_authenticated or request.user.profile.role != 'super_admin':
        messages.error(request, "Access restricted to Super Admins.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, pk=user_id)
        if user_to_delete.username == 'supperadmin' or user_to_delete.id == request.user.id:
            messages.error(request, "Cannot delete protected system user account.")
        else:
            username = user_to_delete.username
            user_to_delete.delete()
            messages.success(request, f"User account '{username}' has been deleted.")
            
    return redirect('user_management')

# ----------------- MAIN VIEWS -----------------

def dashboard(request):
    """
    Landing page that lists all sites and displays overall metrics.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    # Redirect to active site detail page if site is selected and they didn't clear it
    if request.GET.get('clear_site') != '1':
        active_site_id = request.session.get('active_site_id')
        if active_site_id:
            profile = request.user.profile
            if profile.role == 'technician':
                site_exists = profile.assigned_sites.filter(id=active_site_id).exists()
            else:
                site_exists = Site.objects.filter(id=active_site_id).exists()
            if site_exists:
                return redirect('site_detail', site_id=active_site_id)
            else:
                if 'active_site_id' in request.session:
                    del request.session['active_site_id']
                    
    profile = request.user.profile
    if profile.role == 'technician':
        sites = profile.assigned_sites.all().prefetch_related('vehicles')
        total_sites = sites.count()
        total_vehicles = Vehicle.objects.filter(site__in=sites).count()
        total_cameras = Camera.objects.filter(vehicle__site__in=sites).count()
        reachstackers = Vehicle.objects.filter(site__in=sites, vehicle_type='reachstacker').count()
        side_shifters = Vehicle.objects.filter(site__in=sites, vehicle_type='side_shifter').count()
        forklifts = Vehicle.objects.filter(site__in=sites, vehicle_type='forklift').count()
        active_issues = DeviceIssue.objects.filter(vehicle__site__in=sites).exclude(permanent_solution_status='completed').select_related('vehicle', 'vehicle__site', 'assigned_to').order_by('-issue_date_time')
    else:
        sites = Site.objects.all().prefetch_related('vehicles')
        total_sites = sites.count()
        total_vehicles = Vehicle.objects.count()
        total_cameras = Camera.objects.count()
        reachstackers = Vehicle.objects.filter(vehicle_type='reachstacker').count()
        side_shifters = Vehicle.objects.filter(vehicle_type='side_shifter').count()
        forklifts = Vehicle.objects.filter(vehicle_type='forklift').count()
        active_issues = DeviceIssue.objects.exclude(permanent_solution_status='completed').select_related('vehicle', 'vehicle__site', 'assigned_to').order_by('-issue_date_time')
        
    context = {
        'sites': sites,
        'total_sites': total_sites,
        'total_vehicles': total_vehicles,
        'total_cameras': total_cameras,
        'reachstackers': reachstackers,
        'side_shifters': side_shifters,
        'forklifts': forklifts,
        'active_issues': active_issues,
    }
    return render(request, 'vehicles/dashboard.html', context)

def site_detail(request, site_id):
    """
    Details of a specific site showing its cameras, personnel, and a summary.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = request.user.profile
    if profile.role == 'technician':
        if not profile.assigned_sites.filter(id=site_id).exists():
            messages.error(request, "Permission denied for this terminal location.")
            return redirect('dashboard')
            
    site = get_object_or_404(Site.objects.prefetch_related('vehicles__cameras', 'technicians__user', 'present_users'), pk=site_id)
    vehicles = site.vehicles.all()
    assigned_personnel = site.technicians.all()
    present_personnel = site.present_users.all()
    available_users = User.objects.exclude(id__in=present_personnel.values_list('id', flat=True))
    
    # Fetch active issues for this site (not completed)
    active_issues = DeviceIssue.objects.filter(vehicle__site=site).exclude(permanent_solution_status='completed').select_related('vehicle', 'assigned_to').order_by('-issue_date_time')
    
    context = {
        'site': site,
        'vehicles': vehicles,
        'assigned_personnel': assigned_personnel,
        'present_personnel': present_personnel,
        'available_users': available_users,
        'availability_choices': Vehicle.AVAILABILITY_CHOICES,
        'active_issues': active_issues,
    }
    return render(request, 'vehicles/site_detail.html', context)

def site_fleet_deployment(request, site_id):
    """
    Separate page for Active Fleet Deployment of a specific site.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = request.user.profile
    if profile.role == 'technician':
        if not profile.assigned_sites.filter(id=site_id).exists():
            messages.error(request, "Permission denied for this terminal location.")
            return redirect('dashboard')
            
    site = get_object_or_404(Site.objects.prefetch_related('vehicles__cameras', 'vehicles__device_issues'), pk=site_id)
    vehicles = site.vehicles.all()
    
    context = {
        'site': site,
        'vehicles': vehicles,
        'availability_choices': Vehicle.AVAILABILITY_CHOICES,
    }
    return render(request, 'vehicles/fleet_deployment.html', context)

def add_site(request):
    """
    View to add a new site.
    """
    if not request.user.is_authenticated or request.user.profile.role == 'technician':
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard')
        
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
    if not request.user.is_authenticated or request.user.profile.role == 'technician':
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard')
        
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
    if not request.user.is_authenticated or request.user.profile.role != 'super_admin':
        messages.error(request, "Access restricted to Super Admins.")
        return redirect('dashboard')
        
    site = get_object_or_404(Site, pk=site_id)
    if request.method == 'POST':
        site_name = site.name
        site.delete()
        messages.success(request, f"Site '{site_name}' has been deleted.")
        return redirect('dashboard')
    return redirect('site_detail', site_id=site.id)

# ----------------- VEHICLE ACTIONS -----------------

def add_vehicle(request, site_id):
    """
    Add a new vehicle to a site, along with its details and cameras.
    """
    if not request.user.is_authenticated or request.user.profile.role == 'technician':
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard')
        
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
        
        driver_name = request.POST.get('driver_name')
        driver_number = request.POST.get('driver_number')
        availability_status = request.POST.get('availability_status') or 'available'
        
        if not name or not vehicle_type:
            messages.error(request, "Vehicle name and type are required.")
            return render(request, 'vehicles/vehicle_form.html', {'site': site, 'vehicle_types': Vehicle.VEHICLE_TYPES})
            
        try:
            with transaction.atomic():
                vehicle = Vehicle.objects.create(
                    site=site,
                    name=name,
                    vehicle_type=vehicle_type,
                    vehicle_number=vehicle_number,
                    box_number=box_number,
                    device_name=device_name,
                    device_ip=device_ip,
                    device_status=device_status,
                    other_info=other_info,
                    driver_name=driver_name,
                    driver_number=driver_number,
                    availability_status=availability_status
                )
                
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
                
                messages.success(request, f"Vehicle '{vehicle.name}' added successfully.")
                return redirect('site_detail', site_id=site.id)
                
        except Exception as e:
            messages.error(request, f"Error saving vehicle: {e}")
            
    context = {
        'site': site,
        'vehicle_types': Vehicle.VEHICLE_TYPES,
        'availability_choices': Vehicle.AVAILABILITY_CHOICES,
        'action': 'Add'
    }
    return render(request, 'vehicles/vehicle_form.html', context)

def vehicle_detail(request, vehicle_id):
    """
    Detailed dashboard page for a specific vehicle.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    issues = DeviceIssue.objects.filter(vehicle=vehicle).exclude(permanent_solution_status='completed').select_related('assigned_to').order_by('-issue_date_time')
    
    context = {
        'vehicle': vehicle,
        'issues': issues,
        'status_choices': DeviceIssue.STATUS_CHOICES,
    }
    return render(request, 'vehicles/vehicle_detail.html', context)

def edit_vehicle(request, vehicle_id):
    """
    Edit a vehicle's details and cameras.
    """
    if not request.user.is_authenticated or request.user.profile.role == 'technician':
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard')
        
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
        
        driver_name = request.POST.get('driver_name')
        driver_number = request.POST.get('driver_number')
        availability_status = request.POST.get('availability_status') or 'available'
        
        if not name or not vehicle_type:
            messages.error(request, "Vehicle name and type are required.")
            return render(request, 'vehicles/vehicle_form.html', {'site': site, 'vehicle': vehicle, 'vehicle_types': Vehicle.VEHICLE_TYPES, 'availability_choices': Vehicle.AVAILABILITY_CHOICES, 'action': 'Edit'})
            
        try:
            with transaction.atomic():
                vehicle.name = name
                vehicle.vehicle_type = vehicle_type
                vehicle.vehicle_number = vehicle_number
                vehicle.box_number = box_number
                vehicle.device_name = device_name
                vehicle.device_ip = device_ip
                vehicle.device_status = device_status
                vehicle.other_info = other_info
                vehicle.driver_name = driver_name
                vehicle.driver_number = driver_number
                vehicle.availability_status = availability_status
                vehicle.save()
                
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
            
    context = {
        'site': site,
        'vehicle': vehicle,
        'vehicle_types': Vehicle.VEHICLE_TYPES,
        'availability_choices': Vehicle.AVAILABILITY_CHOICES,
        'cameras': vehicle.cameras.all(),
        'action': 'Edit'
    }
    return render(request, 'vehicles/vehicle_form.html', context)

def delete_vehicle(request, vehicle_id):
    """
    Delete a vehicle.
    """
    if not request.user.is_authenticated or request.user.profile.role == 'technician':
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard')
        
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    site_id = vehicle.site.id
    if request.method == 'POST':
        veh_name = vehicle.name
        vehicle.delete()
        messages.success(request, f"Vehicle '{veh_name}' has been deleted.")
    return redirect('site_detail', site_id=site_id)

def update_vehicle_status(request, vehicle_id):
    """
    Endpoint to quickly change the status of a vehicle.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        
        # Technician can only update status if site is allocated to them
        if request.user.profile.role == 'technician' and not request.user.profile.assigned_sites.filter(id=vehicle.site.id).exists():
            messages.error(request, "Unauthorized: Site not allocated.")
            return redirect('dashboard')
            
        status = request.POST.get('availability_status')
        valid_statuses = [choice[0] for choice in Vehicle.AVAILABILITY_CHOICES]
        if status in valid_statuses:
            vehicle.availability_status = status
            vehicle.save()
            messages.success(request, f"Availability of vehicle '{vehicle.name}' changed to {vehicle.get_availability_status_display()}.")
        else:
            messages.error(request, "Invalid status choice.")
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('site_detail', site_id=vehicle.site.id)
    return redirect('dashboard')

# ----------------- DEVICE ISSUE ACTIONS -----------------

def device_issues(request):
    """
    View to list device issue logs (with limit controls).
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = request.user.profile
    limit = request.GET.get('limit', '10')
    if limit not in ['10', '50', '100']:
        limit = '10'
        
    if profile.role == 'technician':
        assigned_sites = profile.assigned_sites.all()
        issues_query = DeviceIssue.objects.filter(vehicle__site__in=assigned_sites).select_related('vehicle__site', 'assigned_to')
        technicians = []
    else:
        issues_query = DeviceIssue.objects.select_related('vehicle__site', 'assigned_to')
        technicians = User.objects.filter(profile__role='technician').order_by('username')
        
    # Filter by persistent site selection if set in session
    active_site_id = request.session.get('active_site_id')
    if active_site_id:
        issues_query = issues_query.filter(vehicle__site_id=active_site_id)
        
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        issues_query = issues_query.filter(issue_date_time__gte=start_date)
    if end_date:
        issues_query = issues_query.filter(issue_date_time__lte=end_date)
        
    issues = issues_query.all()[:int(limit)]
    
    context = {
        'issues': issues,
        'technicians': technicians,
        'status_choices': DeviceIssue.STATUS_CHOICES,
        'limit': limit,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'vehicles/device_issues.html', context)

def add_device_issue(request):
    """
    View to log/add a new device issue.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = request.user.profile
    if request.method == 'POST':
        if profile.role == 'technician':
            messages.error(request, "Technicians cannot log issues.")
            return redirect('device_issues')
            
        vehicle_id = request.POST.get('vehicle_id')
        issue_date_time = request.POST.get('issue_date_time')
        problem_details = request.POST.get('problem_details')
        temp_solution_applied = request.POST.get('temp_solution_applied') == 'on'
        permanent_solution_required = request.POST.get('permanent_solution_required') == 'on'
        permanent_solution_status = request.POST.get('permanent_solution_status') or 'pending'
        assigned_to_id = request.POST.get('assigned_to')
        
        if not vehicle_id or not issue_date_time or not problem_details:
            messages.error(request, "Vehicle, issue date/time, and problem details are required.")
            return redirect('add_device_issue')
            
        try:
            vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
            assigned_user = User.objects.get(pk=assigned_to_id) if assigned_to_id else None
            DeviceIssue.objects.create(
                vehicle=vehicle,
                issue_date_time=issue_date_time,
                problem_details=problem_details,
                temp_solution_applied=temp_solution_applied,
                permanent_solution_required=permanent_solution_required,
                permanent_solution_status=permanent_solution_status,
                assigned_to=assigned_user
            )
            messages.success(request, "Device issue logged successfully.")
            return redirect('device_issues')
        except Exception as e:
            messages.error(request, f"Error logging issue: {e}")
            return redirect('add_device_issue')
            
    # GET request
    if profile.role == 'technician':
        vehicles = []
        technicians = []
    else:
        vehicles = Vehicle.objects.select_related('site')
        technicians = User.objects.filter(profile__role='technician').order_by('username')
        
    context = {
        'vehicles': vehicles,
        'technicians': technicians,
        'status_choices': DeviceIssue.STATUS_CHOICES,
    }
    return render(request, 'vehicles/add_device_issue.html', context)

def allocated_device_issues(request):
    """
    View to list issues allocated to the currently logged in user.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = request.user.profile
    limit = request.GET.get('limit', '10')
    if limit not in ['10', '50', '100']:
        limit = '10'
        
    if profile.role == 'technician':
        assigned_sites = profile.assigned_sites.all()
        issues_query = DeviceIssue.objects.filter(vehicle__site__in=assigned_sites, assigned_to=request.user).select_related('vehicle__site', 'assigned_to')
        technicians = []
    else:
        issues_query = DeviceIssue.objects.filter(assigned_to=request.user).select_related('vehicle__site', 'assigned_to')
        technicians = User.objects.filter(profile__role='technician').order_by('username')
        
    # Filter by persistent site selection if set in session
    active_site_id = request.session.get('active_site_id')
    if active_site_id:
        issues_query = issues_query.filter(vehicle__site_id=active_site_id)
        
    allocated_issues = issues_query.all()[:int(limit)]
    
    context = {
        'allocated_issues': allocated_issues,
        'technicians': technicians,
        'status_choices': DeviceIssue.STATUS_CHOICES,
        'limit': limit,
    }
    return render(request, 'vehicles/allocated_device_issues.html', context)

def update_issue_status(request, issue_id):
    """
    Endpoint to quickly update status and info of an issue.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.method == 'POST':
        issue = get_object_or_404(DeviceIssue, pk=issue_id)
        profile = request.user.profile
        
        # Technician can only update status if site is allocated to them OR they are assigned
        if profile.role == 'technician':
            if not profile.assigned_sites.filter(id=issue.vehicle.site.id).exists() and issue.assigned_to != request.user:
                messages.error(request, "Unauthorized: Site not allocated and not assigned to you.")
                return redirect('device_issues')
            
        status = request.POST.get('permanent_solution_status')
        temp_solution_applied = request.POST.get('temp_solution_applied') == 'on'
        permanent_solution_required = request.POST.get('permanent_solution_required') == 'on'
        
        # Super admin and mid-level can also change assignee
        if profile.role != 'technician':
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id == '':
                issue.assigned_to = None
            elif assigned_to_id:
                issue.assigned_to = get_object_or_404(User, pk=assigned_to_id)
        
        valid_statuses = [choice[0] for choice in DeviceIssue.STATUS_CHOICES]
        if status in valid_statuses:
            issue.permanent_solution_status = status
            issue.temp_solution_applied = temp_solution_applied
            issue.permanent_solution_required = permanent_solution_required
            issue.save()
            messages.success(request, f"Issue for '{issue.vehicle.name}' updated successfully.")
        else:
            messages.error(request, "Invalid status choice.")
            
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'device_issues')

def delete_device_issue(request, issue_id):
    """
    Endpoint to delete a device issue log. Restricted to Super Admin and Mid Level.
    """
    if not request.user.is_authenticated or request.user.profile.role == 'technician':
        messages.error(request, "Unauthorized action.")
        return redirect('device_issues')
        
    issue = get_object_or_404(DeviceIssue, pk=issue_id)
    if request.method == 'POST':
        vehicle_name = issue.vehicle.name
        issue.delete()
        messages.success(request, f"Issue log for vehicle '{vehicle_name}' has been deleted.")
        
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'device_issues')

def edit_user(request, user_id):
    if not request.user.is_authenticated or request.user.profile.role != 'super_admin':
        messages.error(request, "Access restricted to Super Admins.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        user_to_edit = get_object_or_404(User, pk=user_id)
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        assigned_sites_ids = request.POST.getlist('assigned_sites[]')
        
        try:
            with transaction.atomic():
                user_to_edit.email = email
                if password:
                    user_to_edit.set_password(password)
                user_to_edit.save()
                
                # Protect role of weboccultadmin from being changed
                profile = user_to_edit.profile
                if user_to_edit.username != 'weboccultadmin':
                    profile.role = role
                
                # Update assigned sites
                if profile.role == 'technician':
                    sites = Site.objects.filter(id__in=assigned_sites_ids)
                    profile.assigned_sites.set(sites)
                else:
                    profile.assigned_sites.clear()
                profile.save()
                
            messages.success(request, f"User account '{user_to_edit.username}' updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating user: {e}")
            
    return redirect('user_management')

def add_site_person(request, site_id):
    """
    Check-in / add a person physically to a site.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    site = get_object_or_404(Site, pk=site_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user_to_add = get_object_or_404(User, pk=user_id)
            site.present_users.add(user_to_add)
            messages.success(request, f"User '{user_to_add.username}' marked as present on site.")
        else:
            messages.error(request, "No user selected.")
            
    return redirect('site_detail', site_id=site.id)

def remove_site_person(request, site_id, user_id):
    """
    Check-out / remove a person physically from a site.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    site = get_object_or_404(Site, pk=site_id)
    user_to_remove = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        site.present_users.remove(user_to_remove)
        messages.success(request, f"User '{user_to_remove.username}' checked out / removed from site.")
        
    return redirect('site_detail', site_id=site.id)

def vehicle_management(request):
    """
    View to list all vehicles across sites (filtered by user role/assigned sites).
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = request.user.profile
    if profile.role == 'technician':
        sites = profile.assigned_sites.all()
        vehicles = Vehicle.objects.filter(site__in=sites).select_related('site')
    else:
        vehicles = Vehicle.objects.all().select_related('site')
        
    # Filter by the globally selected active site if one is chosen
    active_site_id = request.session.get('active_site_id')
    if active_site_id:
        if profile.role == 'technician':
            if profile.assigned_sites.filter(id=active_site_id).exists():
                vehicles = vehicles.filter(site_id=active_site_id)
        else:
            vehicles = vehicles.filter(site_id=active_site_id)
            
    context = {
        'vehicles': vehicles,
        'availability_choices': Vehicle.AVAILABILITY_CHOICES,
    }
    return render(request, 'vehicles/vehicle_management.html', context)
