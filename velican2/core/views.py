from typing import Any, Dict
from django import http
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic as generic_views
from django.views.generic import edit as edit_views 
from django.utils.translation import gettext as _
from pathlib import Path

from velican2.engines import pelican

from . import models
from . import forms

def index(request: http.HttpRequest):
    return render(request, "index.html")


class Start(LoginRequiredMixin, generic_views.FormView):
    form_class = forms.StartForm
    template_name = "start.html"
    success_url = reverse_lazy("core:add_post")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(
            domain=settings.DOMAIN,
            pelican_themes=pelican.models.Theme.objects.filter(image__isnull=False),
            **kwargs)


class SiteMixin:
    def dispatch(self, request, site:str, *args, **kwargs):
        try:
            self.site = models.Site.objects.filter(admin=request.user, domain=site).get()
        except models.Site.DoesNotExist:
            messages.info(request, _("Site required"))
            return redirect("core:start")
        return super().dispatch(request, *args, site=site, **kwargs)
    
    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(*args, **kwargs, site=self.site)


class Site(SiteMixin, generic_views.DetailView):
    template_name = "site.html"

    def get_object(self):
        return self.site
    
    def get_context_data(self, *args, **kwargs):
        
        return super().get_context_data(
            *args,
            posts_num = models.Post.objects.filter(site=self.site).count(),
            **kwargs)


class Sites(generic_views.ListView):
    template_name = "sites.html"

    def get_queryset(self):
        return models.Site.objects.filter(admin=self.request.user)

    def get(self, request):
        if models.Site.objects.filter(admin=request.user).count() == 1:
            return redirect('core:site', models.Site.objects.filter(admin=request.user).get().domain)
        return super().get(request)



class Post(SiteMixin, edit_views.CreateView):
    form_class = forms.PostForm
    template_name = "post.html"


def publish(request: http.HttpRequest, site: str):
    def as_bool(value: str):
        return value.lower() in ("1", "true", "yes")

    return get_object_or_404(models.Site, domain=site).publish(
        request.user,
        force=as_bool(request.GET.get("force", "False")),
        purge=as_bool(request.GET.get("purge", "False")),
    )

def domains(request: http.HttpRequest):
    return http.JsonResponse(
        models.Site.objects.all().values_list("domain", flat=True))

def page(request: http.HttpRequest):
    return render(request, Path(request.path).name)
