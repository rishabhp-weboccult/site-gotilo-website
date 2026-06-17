from django import template

register = template.Library()

@register.simple_tag
def filter_by_type(vehicles, vehicle_type):
    """
    Filter a list of vehicles by their type.
    """
    if not vehicles:
        return []
    # Handles querysets or lists
    if hasattr(vehicles, 'filter'):
        return vehicles.filter(vehicle_type=vehicle_type)
    return [v for v in vehicles if v.vehicle_type == vehicle_type]

@register.simple_tag
def get_cameras_count(vehicles):
    """
    Get the total number of cameras for a collection of vehicles.
    """
    if not vehicles:
        return 0
    count = 0
    for v in vehicles:
        # If prefetch_related is active, cameras.all() is cached and len is faster
        if hasattr(v, '_prefetched_objects_cache') and 'cameras' in v._prefetched_objects_cache:
            count += len(v.cameras.all())
        else:
            count += v.cameras.count()
    return count
