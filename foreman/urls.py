from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
      #auth urls
    path('accounts/login/', views.login_view, name="login"),
    path('accounts/register', views.register, name="register"),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('sites/', views.site_list, name='site_list'),
    path('sites/new/', views.site_create, name='site_create'),
    path('sites/<int:pk>/', views.site_detail, name='site_detail'),
    path('sites/<int:pk>/edit/', views.site_update, name='site_update'),
    path('sites/<int:pk>/delete/', views.site_delete, name='site_delete'),
    
    path('human-resources/', views.human_resource_list, name='human_resource_list'),
    path('human-resources/add/', views.add_human_resource, name='add_human_resource'),
    path('human-resources/<int:pk>/edit/', views.edit_human_resource, name='edit_human_resource'),
    path('human-resources/<int:pk>/delete/', views.delete_human_resource, name='delete_human_resource'),
    
    path('assets/', views.asset_list, name='asset_management'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/update/', views.asset_update, name='asset_update'),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    path('assets/<int:pk>/maintenance/', views.asset_maintenance, name='asset_maintenance'),
]





#media handler
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)