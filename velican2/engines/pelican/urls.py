"""velican2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
"""
from django.contrib import admin
from django.urls import path, include
from .views import SettingsList, SettingsDetail, ThemeList

app_name="pelican"
urlpatterns = [
    path("", SettingsList.as_view(), name="settings"),
    path("<int:id>/", SettingsDetail.as_view(), name="settings"),
    path("<int:id>/themes/", ThemeList.as_view(), name="themes"),
]
