from typing import Any, Dict
from django import forms

from django.core.exceptions import ValidationError
from django.conf import settings

from markdownx.fields import MarkdownxFormField

from .models import Site, Post
from velican2.engines.pelican import models as pelican

class StartForm(forms.Form):
    title = forms.CharField(max_length=128)
    subtitle = forms.CharField(max_length=256, required=False)
    own_domain = forms.CharField(max_length=100, required=False)
    # domain = forms.CharField(max_length=100)
    subdomain = forms.CharField(max_length=100, required=False)
    pelican_theme = forms.ChoiceField(choices=pelican.Theme.objects.all().values_list('name', 'name'), required=True)  # TODO: change to not-required once more engines are ready

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        own_domain = cleaned_data.get("own_domain")
        subdomain = cleaned_data.get("subdomain")

        if not (own_domain or subdomain):
            self.add_error('own_domain', ValidationError("Specify either your own domain or a subdomain"))
            self.add_error('subdomain', ValidationError("Specify either your own domain or a subdomain"))

    def save(self):
        """Should return an object (class) that will be used in redirect URL contruction"""
        data = self.cleaned_data
        site_kwargs = {}
        if data.get('pelican_theme'):
            site_kwargs['engine'] = "pelican"
        if data.get('own_domain'):
            site_kwargs['domain'] = data.get("own_domain")
        else:
            site_kwargs['domain'] = data.get("subdomain") + "." + settings.DOMAIN
        site_kwargs['title'] = data.get('title')
        site_kwargs['subtitle'] = data.get('subtitle')
        # create site and the engine's settings will auto-create with it
        site = Site.objects.create(**site_kwargs)

        if data.get('pelican_theme'):
            pelican = pelican.Settings.objects.get(site=site)
            pelican.theme = pelican.Theme.objects.get(name=data.get('pelican_theme'))
            pelican.save()

        return site


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "lang", "description", "punchline", "content", )

    content = MarkdownxFormField()