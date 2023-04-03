from django import http
from django.contrib import auth
from django.shortcuts import render, get_object_or_404
from . import models


def publish(request: http.Request, site: str):
    get_object_or_404(models.Site, domain=site).publish(
        request.user, preview=False)


def preview(request: http.Request, site: str):
    get_object_or_404(models.Site, domain=site).publish(
        request.user, preview=True)


def domains(request: http.Request):
    return http.JsonResponse(
        models.Site.objects.all().values_list("domain", flat=True))