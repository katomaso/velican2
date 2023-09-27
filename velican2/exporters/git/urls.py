from django.urls import path
from . import views

app_name = "git"

urlpatterns = [
    path('<str:site>/connect', views.Create.as_view(), name="connect"),
]
