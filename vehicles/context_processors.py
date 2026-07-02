from .models import Site

def sites_processor(request):
    """
    Context processor to make sites and the active site available globally in templates,
    filtering for technicians to only show their assigned locations.
    """
    context = {}
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'technician':
                all_sites = profile.assigned_sites.all().order_by('name')
            else:
                all_sites = Site.objects.all().order_by('name')
            context['all_sites'] = all_sites
            
            # Determine active site ID
            active_site_id = None
            
            # 1. Check if user wants to explicitly clear active site context
            if request.GET.get('clear_site') == '1':
                if 'active_site_id' in request.session:
                    del request.session['active_site_id']
            else:
                # 2. Check if active site is in the URL path, e.g. /site/123/ or /site/123/fleet/
                path_parts = request.path.strip('/').split('/')
                if len(path_parts) >= 2 and path_parts[0] == 'site':
                    try:
                        active_site_id = int(path_parts[1])
                        # Save it in session
                        request.session['active_site_id'] = active_site_id
                    except ValueError:
                        pass
                
                # 3. If not in path, retrieve from session
                if not active_site_id:
                    active_site_id = request.session.get('active_site_id')
                
                # Auto-select if there is only 1 site available (e.g. for technicians)
                if not active_site_id and all_sites.count() == 1:
                    active_site_id = all_sites.first().id
                    
                # If we found an active site ID, get the object and inject it
                if active_site_id:
                    try:
                        active_site = all_sites.get(id=active_site_id)
                        context['site'] = active_site
                    except Site.DoesNotExist:
                        # Clear session if site doesn't exist or is not authorized
                        if 'active_site_id' in request.session:
                            del request.session['active_site_id']
                        
        except Exception:
            pass
            
    # Default fallback
    if 'all_sites' not in context:
        context['all_sites'] = Site.objects.all().order_by('name')
        
    return context
