from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('domains/', views.domains),
    path("legal.html", views.page),
]
