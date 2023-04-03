from datetime import datetime, timedelta
from pathlib import Path

from django.db import models
from django.contrib import auth
from django.contrib.auth import models as auth


class UpdateException(Exception):
    pass


class Site(models.Model):
    domain = models.CharField(max_length=32, primary_key=True)
    path = models.CharField(max_length=32, primary_key=True)
    staff = models.ManyToManyField(auth.User)
    lang = models.CharField(max_length=48, default="cs_CZ")
    timezone = models.CharField(max_length=128, default="Europe/Prague")

    title = models.CharField(max_length=128, null=True)
    subtitle = models.CharField(max_length=128, null=True)
    logo = models.ImageField(
        upload_to=lambda instance, filename: f"{instance.domain}.{Path(filename).suffix}")
    
    engine = models.CharField(max_length=12, null=False,
        choices=(("pelican", "Pelican")), default="pelican")

    def get_engine(self):
        if self.engine == "pelican":
            from velican2.pelican.models import Pelican
            return Pelican.objects.get(site=self)

    def publish(self, user: auth.User, preview=False):
        return Publish.get_running() or Publish.objects.create(
            site=self,
            user=user,
        )


class Category(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, primary_key=True)
    slug = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Publish(models.Model):
    site = models.ForeignKey(Site, primary_key=True, on_delete=models.CASCADE)
    preview = models.CharField(max_length=False)
    started = models.DateTimeField(auto_now_add=True, primary_key=True)
    finished = models.DateTimeField(null=True)
    success =  models.BooleanField(null=True)
    message = models.CharField(max_length=512)

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
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
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

    def save(self, user=None, **kwargs):
        if not self.can_edit(user):
            raise PermissionError("You are not a part of staff of the site")
        if self.id:
            prev = Post.objects.get(id=self.id)
            if prev.updated > self.updated:
                raise UpdateException("You are editing an outdated version")
        super().save(self, **kwargs)

    def get_url(self):
        return self.site.get_engine().get_page_url(self.site, self)


class Post(Page):
    title = models.CharField(max_length=128)
    category = models.ForeignKey(Category)
    description = models.TextField()
    author = models.ForeignKey(auth.User)
    draft = models.BooleanField(default=True)
    
    def save(self, user=None, **kwargs):
        if not self.can_edit(user):
            raise PermissionError("You are not a part of staff of the site")
        if not self.author:
            self.author - user
        if self.id:
            prev = Post.objects.get(id=self.id)
            if prev.updated > self.updated:
                raise UpdateException("You are editing an outdated version")
        super().save(**kwargs)

    def get_url(self):
        return self.site.get_engine().get_post_url(self.site, self)
