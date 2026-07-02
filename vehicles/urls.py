from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard & Site views
    path('', views.dashboard, name='dashboard'),
    path('site/add/', views.add_site, name='add_site'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('site/<int:site_id>/fleet/', views.site_fleet_deployment, name='site_fleet_deployment'),
    path('site/<int:site_id>/edit/', views.edit_site, name='edit_site'),
    path('site/<int:site_id>/delete/', views.delete_site, name='delete_site'),
    
    # Vehicle actions
    path('site/<int:site_id>/person/add/', views.add_site_person, name='add_site_person'),
    path('site/<int:site_id>/person/<int:user_id>/remove/', views.remove_site_person, name='remove_site_person'),
    path('site/<int:site_id>/vehicle/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicle/<int:vehicle_id>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/<int:vehicle_id>/delete/', views.delete_vehicle, name='delete_vehicle'),
    path('vehicle/<int:vehicle_id>/status/', views.update_vehicle_status, name='update_vehicle_status'),
    path('vehicle/<int:vehicle_id>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/', views.vehicle_management, name='vehicle_management'),
    
    # Device issue tracking actions
    path('issues/', views.device_issues, name='device_issues'),
    path('issues/add/', views.add_device_issue, name='add_device_issue'),
    path('issues/allocated/', views.allocated_device_issues, name='allocated_device_issues'),
    path('issues/<int:issue_id>/update/', views.update_issue_status, name='update_issue_status'),
    path('issues/<int:issue_id>/delete/', views.delete_device_issue, name='delete_device_issue'),
    
    # Authentication routes
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Administration routes (Super Admin only)
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
