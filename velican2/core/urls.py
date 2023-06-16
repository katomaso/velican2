from django.urls import path
from . import views

urlpatterns = [
    path('domains/', views.domains),
    path("privacy.html", views.page),
]
