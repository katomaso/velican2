from datetime import datetime, timedelta
from typing import (Optional, Iterable)
from pathlib import Path

from django.db import models
from django.conf import settings
from django.contrib import auth


class UpdateException(Exception):
    pass


class Site(models.Model):
    domain = models.CharField(max_length=32, primary_key=True, default="example.com")
    owner = models.ForeignKey(auth.User)
    staff = models.ManyToManyField(auth.User)
    theme_name = models.CharField(max_length=32, default="default")
    lang = models.CharField(max_length=48, default="cs_CZ")
    timezone = models.CharField(max_length=128, default="Europe/Prague")
    title = models.CharField(max_length=128, null=True)
    subtitle = models.CharField(max_length=128, null=True)
    twitter = models.CharField(max_length=128, null=True)
    linkedin = models.CharField(max_length=128, null=True)
    github = models.CharField(max_length=128, null=True)


class Theme(models.Model):
    name = models.CharField(max_length=32, primary_key=True)


class Category(models.Model):
    site = models.ForeignKey(Site)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Publish(models.Model):
    site = models.ForeignKey(Site, primary_key=True)
    preview = models.CharField(max_length=False)
    started = models.DateTimeField(auto_now_add=True, primary_key=True)
    finished = models.DateTimeField(auto_now=True)
    result = models.CharField(max_length=512)
    failed =  models.Bool(default=False)

    @classmethod
    def get_running(cls, site: str, preview=False):
        try:
            return Publish.objects.filter(
                site=site,
                preview=preview,
                started__gt=datetime.utcnow()-timedelta(minute=1),
                finished__isnone=True).get()
        except Publish.DoesNotExist:
            return None
        
    def save(self, **kwargs):
        if not self.id:  # new record
            if Publish.get_running() is not None:
                raise UpdateException("Publish is already running")
        super().save(**kwargs)


class Page(models.Model):
    site = models.ForeignKey(Site)
    slug = models.CharField(max_length=64)
    title = models.CharField(max_length=128)
    lang = models.CharField(max_length=5)
    content = models.Text()
    created = models.DateTimeField(auto_add_now=datetime.utcnow)
    updated = models.DateTimeField(auto_now=datetime.utcnow)

    class Meta:
        unique_together = (('site_id', 'slug', 'lang'), )

    def can_edit(self, user: auth.User):
        return self.site.staff.contains(user)

    def get_file_path(self):
        return self.site.content_dir / "articles" / self.slug + ".md"

    def save(self, user=None, **kwargs):
        if not self.can_edit(user):
            raise PermissionError("You are not a part of staff of the site")
        if self.id:
            prev = Post.objects.get(id=self.id)
            if prev.updated > self.updated:
                raise UpdateException("You are editing an outdated version")
        super().save(self, **kwargs)


class Post(Page):
    author = models.ForeignKey(auth.User)
    title = models.CharField(max_length=128)
    category = models.ForeignKey(Category)
    description = models.TextField()
    draft = models.BooleanField(default=True)

    def get_file_path(self):
        return self.site.content_dir / "pages" / self.slug + ".md"
    
    def save(self, user=None, **kwargs):
        if not self.can_edit(user):
            raise PermissionError("You are not a part of staff of the site")
        if self.id:
            prev = Post.objects.get(id=self.id)
            if prev.updated > self.updated:
                raise UpdateException("You are editing an outdated version")
        super().save(**kwargs)
