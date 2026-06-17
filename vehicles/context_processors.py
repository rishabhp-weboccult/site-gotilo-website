from .models import Site

def sites_processor(request):
    """
    Context processor to make all sites available globally in templates,
    allowing the navbar site-selector dropdown to render on any page.
    """
    return {
        'all_sites': Site.objects.all().order_by('name')
    }
