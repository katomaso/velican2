from datetime import datetime, timedelta
from pathlib import Path

from django.db import models
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import models as auth
from django.core.validators import validate_unicode_slug, RegexValidator
from django.utils.translation import gettext as _

class UpdateException(Exception):
    pass

LANG_CHOICES = (
    ("cs_CZ", "cs"),
    ("en_US", "en"),
)


class Site(models.Model):
    domain = models.CharField(max_length=32, db_index=True, help_text="Example: example.com", validators=(RegexValidator(regex=r'^([a-zA-Z0-9_\-]+\.?)+$'), ))
    path = models.CharField(max_length=32, default="", blank=True, help_text="Fill only if your site is under a path (e.g. \"/blog\")", validators=(RegexValidator(regex=r'^([a-zA-Z0-9_\-]+/?)*$'), ))
    staff = models.ManyToManyField(auth.User)
    lang = models.CharField(max_length=48, choices=LANG_CHOICES)
    timezone = models.CharField(max_length=128, default="Europe/Prague")

    title = models.CharField(max_length=128, null=True)
    subtitle = models.CharField(max_length=128, null=True)
    logo = models.ImageField(blank=True, null=True, upload_to=lambda self, filename: settings.MEDIA_ROOT / self.domain / self.path.strip("/") / filename)

    allow_crawlers = models.BooleanField(default=True, help_text="Allow search engines to index this page")
    allow_training = models.BooleanField(default=True, help_text="Allow AI engines to index this page")

    engine = models.CharField(max_length=12, null=False,
        choices=(("pelican", "Pelican"), ), default="pelican")

    secure = models.BooleanField(default=True, help_text="The site is served via secured connection https")

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")
        unique_together = [['domain', 'path']]

    __str__ = lambda self: self.domain + self.path

    def get_engine(self):
        if self.engine == "pelican":
            from velican2.pelican.models import Settings
            return Settings.objects.get(site=self)

    def publish(self, user: auth.User, preview=False):
        return Publish.get_running() or Publish.objects.create(
            site=self,
            user=user,
        )

    def save(self, **kwargs):
        self.domain = self.domain.strip(".")
        if self.path.strip("/"):
            self.path = "/" + self.path.strip("/")
        super().save(**kwargs)

    def absolutize(self, path):
        return ("https://" if self.secure else "http://") + self.domain + self.path


class Category(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    slug = models.CharField(max_length=32, validators=(validate_unicode_slug,))
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = [['site', 'slug']]

    def __str__(self):
        return self.name


class Publish(models.Model):
    site = models.ForeignKey(Site, db_index=True, on_delete=models.CASCADE)
    preview = models.BooleanField(default=False)
    started = models.DateTimeField(auto_now_add=True, db_index=True)
    finished = models.DateTimeField(null=True)
    success =  models.BooleanField(null=True)
    message = models.CharField(max_length=512)

    class Meta:
        verbose_name = _("Publish")
        verbose_name_plural = _("Publish")

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
    slug = models.CharField(max_length=64, validators=(validate_unicode_slug,))
    title = models.CharField(max_length=128)
    lang = models.CharField(max_length=5, choices=LANG_CHOICES)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=datetime.utcnow)
    updated = models.DateTimeField(auto_now=datetime.utcnow)

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")

    class Meta:
        unique_together = (('site', 'slug', 'lang'), )

    def can_edit(self, user: auth.User):
        return self.site.staff.contains(user)

    def save(self, user=None, **kwargs):
        if user and not self.can_edit(user):
            raise PermissionError("You are not a part of staff of the site")
        if self.id:
            prev = Post.objects.get(id=self.id)
            if prev.updated > self.updated:
                raise UpdateException("You are editing an outdated version")
        super().save(self, **kwargs)

    def get_url(self):
        return self.site.get_engine().get_page_url(self.site, self)


class Post(Page):
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    author = models.ForeignKey(auth.User, null=True, on_delete=models.SET_NULL)
    description = models.TextField()
    punchline = models.TextField(blank=True, help_text="Punchline for social media. Defaults to description.")
    draft = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    def save(self, user=None, **kwargs):
        if user and not self.can_edit(user):
            raise PermissionError("You are not a part of staff of the site")
        if user and not self.author:
            self.author = user
        if self.id:
            prev = Post.objects.get(id=self.id)
            if prev.updated > self.updated:
                raise UpdateException("You are editing an outdated version")
        super().save(**kwargs)

    def get_url(self):
        return self.site.get_engine().get_post_url(self.site, self)
