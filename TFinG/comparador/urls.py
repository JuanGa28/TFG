# comparador/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.empezar, name='empezar'),
]
