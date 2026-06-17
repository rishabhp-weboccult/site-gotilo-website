from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('site/add/', views.add_site, name='add_site'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('site/<int:site_id>/edit/', views.edit_site, name='edit_site'),
    path('site/<int:site_id>/delete/', views.delete_site, name='delete_site'),
    path('site/<int:site_id>/vehicle/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicle/<int:vehicle_id>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/<int:vehicle_id>/delete/', views.delete_vehicle, name='delete_vehicle'),
]
