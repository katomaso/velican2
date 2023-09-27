from typing import Any
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.views import generic as views
from django.forms import ModelForm, ValidationError

from velican2.core import views as core

from . import models

class StartForm(ModelForm):
    class Meta:
        model = models.Settings
        fields = ('username', 'password', 'repository')

    def clean(self) -> dict[str, Any]:
        data = super().clean()
        git = models.Settings(
            site=self.initial['site'],
            repository=data['repository'],
            username=data['username'],
            password=data['password'])
        if not git.ensure_repository():
            raise ValidationError("Could not clone/init the repository")
        self.instance.site = self.initial['site']
        return data


class Create(core.SiteMixin, views.CreateView):
    form_class = StartForm
    template_name = "git/connect.html"

    def get_initial(self) -> dict[str, Any]:
        return {'site': self.site}

    def get_success_url(self):
        return reverse("core:site", kwargs={'site': self.site.urn})
