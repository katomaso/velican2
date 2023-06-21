from django import http
from django.shortcuts import render, get_object_or_404

from pathlib import Path

from . import models

def index(request: http.HttpRequest):
    return render(request, "index.html")

def publish(request: http.HttpRequest, site: str):
    def as_bool(value: str):
        return value.lower() in ("1", "true", "yes")

    get_object_or_404(models.Site, domain=site).publish(
        request.user,
        force=as_bool(request.GET.get("force", "False")),
        purge=as_bool(request.GET.get("purge", "False")),
    )

def domains(request: http.HttpRequest):
    return http.JsonResponse(
        models.Site.objects.all().values_list("domain", flat=True))

def page(request: http.HttpRequest):
    return render(request, Path(request.path).name)
