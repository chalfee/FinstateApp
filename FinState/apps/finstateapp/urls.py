from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('reports', views.reports, name='reports'),
    path('holding_registration', views.holding_registration, name='holding_registration'),
    path('holding/<holding_id>/add_factory', views.add_factory, name='add_factory'),
    path('factory', views.factory, name='factory'),
    path('register', views.register, name='register'),
    path('', include('django.contrib.auth.urls')),
    path('activate/<slug:uidb64>/<slug:token>/', views.activate, name='activate'),
]