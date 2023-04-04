from django import http
from django.shortcuts import render, get_object_or_404
from . import models


def publish(request: http.HttpRequest, site: str):
    get_object_or_404(models.Site, domain=site).publish(
        request.user, preview=False)


def preview(request: http.HttpRequest, site: str):
    get_object_or_404(models.Site, domain=site).publish(
        request.user, preview=True)


def domains(request: http.HttpRequest):
    return http.JsonResponse(
        models.Site.objects.all().values_list("domain", flat=True))