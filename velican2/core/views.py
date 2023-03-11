from django import http
from django.contrib import auth
from django.shortcuts import render, get_object_or_404
from . import models

def _publish(site: models.Site, user: auth.User, preview: bool):
    publish = models.Publish(
        user=user,
        site=site,
        )


def publish(request: http.Request, site: str):
    _publish(get_object_or_404(models.Site, domain=site), request.user, preview=False)

def preview(request: http.Request, site: str):
    _publish(get_object_or_404(models.Site, domain=site), request.user, preview=True)
