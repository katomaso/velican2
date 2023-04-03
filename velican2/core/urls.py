from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('domains/', views.domains),
    path('publish/<site>/', views.publish),
    path('preview/<site>/', views.preview),
]
