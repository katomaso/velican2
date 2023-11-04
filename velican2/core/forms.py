from typing import Any, Dict
from datetime import date
from django import forms

from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.conf import settings
from django.contrib.auth import models as auth

from martor.fields import MartorFormField

from . import logger
from .models import Category, Site, Post, Publish
from ..engines.pelican import models as pelican


class StartForm(forms.Form):
    title = forms.CharField(max_length=128)
    subtitle = forms.CharField(max_length=256, required=False)
    own_domain = forms.CharField(max_length=100, required=False)
    subdomain = forms.CharField(max_length=100, required=False)
    pelican_theme = forms.ChoiceField(choices=lambda: pelican.Theme.objects.all().values_list('name', 'name'), required=True)  # TODO: change to not-required once more engines are ready

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        own_domain = cleaned_data.get("own_domain")
        subdomain = cleaned_data.get("subdomain")

        if not (own_domain or subdomain):
            self.add_error('own_domain', ValidationError("Specify either your own domain or a subdomain"))
            self.add_error('subdomain', ValidationError("Specify either your own domain or a subdomain"))

    @atomic
    def save(self, admin: auth.User):
        """Should return an object (class) that will be used in redirect URL contruction"""
        data = self.cleaned_data
        logger.info(data)
        site_kwargs = {"admin": admin}
        if data.get('pelican_theme'):
            site_kwargs['engine'] = "pelican"
        if data.get('own_domain'):
            site_kwargs['urn'] = data.get("own_domain")
        else:
            site_kwargs['urn'] = data.get("subdomain") + "." + settings.DOMAIN
        site_kwargs['title'] = data.get('title')
        site_kwargs['subtitle'] = data.get('subtitle')
        # create site and the engine's settings will auto-create with it
        site = Site.objects.create(**site_kwargs)

        if data.get('pelican_theme'):
            pelican, _ = pelican.Settings.objects.get_or_create(site=site)
            pelican.theme = pelican.Theme.objects.get(name=data.get('pelican_theme'))
            pelican.save()
        return site


class SiteEditForm(forms.ModelForm):
    class Meta:
        model = Site
        exclude = ("urn", "admin", "staff")


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "lang", "description", "category", "translation_of")


class CategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", )


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "lang", "draft", "description", "punchline", "content", "broadcast", "updated")
    action = forms.CharField(initial="save")
    content = MartorFormField()

    def clean(self):
        self.cleaned_data['updated'] = date.today()
        if self.cleaned_data['action'] == "publish":
            self.cleaned_data['draft'] = False
            self.publish = Publish(site=self.initial['site'])
            self.publish.clean()
        return super().clean()
    
    def save(self, commit=True):
        instance = super().save(commit)
        if hasattr(self, 'publish'):
            instance.publish(commit=True)
            self.publish.post = instance
            self.publish.save()
        return instance