import threading

from pathlib import Path

from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
from django.core.validators import validate_unicode_slug, RegexValidator
from django.utils.translation import gettext as _

from velican2 import engines
from velican2 import deployers

from .managers import PublishManager
from . import logger

class UpdateException(Exception):
    pass

LANG_CHOICES = (
    ("cs_CZ", "cs"),
    ("en_US", "en"),
)


def site_logo_upload(site, filename):
    return Path(settings.MEDIA_ROOT / site.domain / site.path.strip("/") / filename).with_stem("logo")

def site_heading_upload(site, filename):
    return Path(settings.MEDIA_ROOT / site.domain / site.path.strip("/") / filename).with_stem("heading")

ENGINE_CHOICES = tuple((engine, engine.title()) for engine in engines.engines)

class Site(models.Model):
    domain = models.CharField(max_length=32, db_index=True, help_text="Example: example.com", validators=(RegexValidator(regex=r'^([a-zA-Z0-9_\-]+\.?)+$'), ))
    path = models.CharField(max_length=32, default="", blank=True, help_text="Fill only if your site is under a path (e.g. \"/blog\")", validators=(RegexValidator(regex=r'^([a-zA-Z0-9_\-]+/?)*$'), ))
    admin = models.ForeignKey(auth.User, on_delete=models.CASCADE, related_name="+")
    staff = models.ManyToManyField(auth.User)
    lang = models.CharField(max_length=48, choices=LANG_CHOICES)
    timezone = models.CharField(max_length=128, default="Europe/Prague")
    secure = models.BooleanField(default=True, help_text="The site is served via secured connection https")

    title = models.CharField(max_length=128, null=True)
    subtitle = models.CharField(max_length=128, null=True)
    logo = models.ImageField(blank=True, null=True, upload_to=site_logo_upload)
    heading = models.ImageField(blank=True, null=True, upload_to=site_heading_upload)

    allow_crawlers = models.BooleanField(default=True, help_text="Allow search engines to index this page")
    allow_training = models.BooleanField(default=True, help_text="Allow AI engines to index this page")

    engine = models.CharField(max_length=12, null=False,
        choices=ENGINE_CHOICES, default=engines.engines[0])

    deployment = models.CharField(max_length=12, null=False,
        choices=(
            ("aws", "AWS CloudFront"),
            ("caddy", "local Caddy server")
        ))

    webmentions = models.BooleanField(default=False, help_text="Should it use builtin webmentions service")
    webmentions_external = models.CharField(max_length=256, blank=True, null=True, help_text="URL of an external webmentions service")

    matomo = models.BooleanField(default=False, help_text="Should it use builtin tracking service")
    matomo_external = models.CharField(max_length=256, null=True, blank=True, help_text="URL of an external tracking service")
    matomo_external_id = models.CharField(max_length=64, null=True, blank=True, help_text="SITE_ID for the external tracking service")

    # google_adsense = 
    google_analytics_code = models.CharField(max_length=64, null=True, blank=True, help_text="Your google analytics code UA-XYZ")

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")
        unique_together = [['domain', 'path']]

    __str__ = lambda self: self.domain + self.path

    @property
    def posts(self):
        return Post.objects.all().filter(site=self)

    @property
    def pages(self):
        return Page.objects.all().filter(site=self)

    def get_engine(self):
        return engines.get_engine(self.engine)

    def get_deployer(self):
        return deployers.get_deployer(self.deployment)

    def publish(self, user: auth.User, **kwargs):
        return Publish.get_running() or Publish.objects.create(
            site=self,
            user=user,
            **kwargs
        )

    def save(self, **kwargs):
        self.domain = self.domain.strip(".")
        if self.path.strip("/"):
            self.path = "/" + self.path.strip("/")
        return super().save(**kwargs)

    def delete(self, **kwargs):
        self.site.get_engine().delete(site=self)
        self.site.get_deployer().delete(site=self)
        return super().delete(**kwargs)

    def absolutize(self, path):
        return ("https://" if self.secure else "http://") + self.domain + self.path

    def can_add_content(self, user: auth.User):
        return self.admin == user or self.staff.contains(user)

    def can_manage(self, user: auth.User):
        return self.admin == user


class Category(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    slug = models.CharField(max_length=32, validators=(validate_unicode_slug,))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = [['site', 'slug']]

    def __str__(self):
        return self.name


class Link(models.Model):
    """Links appear in the main menu beside your Pages but links lead (mainly) outside of your domain."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    url = models.CharField(max_length=128)

    __str__ = lambda self: self.title

    def save(self, **kwargs):
        if not self.url.startswith("http"):
            self.url = "https://" + self.url
        return super().save(**kwargs)


class Social(models.Model):
    """Links to social media of the creator"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    url = models.CharField(max_length=128)

    __str__ = lambda self: self.title

    def save(self, **kwargs):
        if not self.url.startswith("http"):
            self.url = "https://" + self.url
        return super().save(**kwargs)


def content_heading_upload(content, filename):
    return Path(settings.MEDIA_ROOT / content.site.domain / content.slug / filename).with_stem("heading")

class Content(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    slug = models.CharField(max_length=64, validators=(validate_unicode_slug,))
    lang = models.CharField(max_length=5, choices=LANG_CHOICES)
    content = models.TextField()
    created = models.DateTimeField()
    updated = models.DateTimeField()
    heading = models.ImageField(blank=True, null=True, upload_to=content_heading_upload)

    __str__ = lambda self: self.title

    class Meta:
        abstract = True

    # For some unknown reason the prev.updated is always like 90 seconds ahead
    def clean(self):
        if self.id: # model aready exists
            prev = Post.objects.get(id=self.id)
            logger.debug(f"prev.updated {prev.updated} SHOULD BE <= self.updated {self.updated}")
            if prev.updated > self.updated:
                raise ValidationError("You are editing an outdated version")
        return super().clean()

    def can_edit(self, user: auth.User):
        return self.site.can_add_content(user)

    def save(self, user=None, **kwargs):
        if not self.id:
            self.created = datetime.now()
        if user and not self.can_edit(user):
            raise PermissionError("You don't have edit rights on this")
        self.updated = datetime.now()
        super().save(**kwargs)


class Page(Content):
    """Page will appear in the top-menu of your main page (and other pages).
    It is static pages that has value through the whole tile such as "about-me" and "services".
    """
    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        unique_together = (('site', 'slug', 'lang'), )

    def get_url(self, absolute=False):
        return self.site.get_engine().get_page_url(self.site, self, absolute=absolute)
    
    def delete(self, **kwargs):
        self.site.get_engine().delete(self.site, page=self)
        self.site.get_deployer().delete(self.site, page=self)
        return super().delete(**kwargs)


class Post(Content):
    """Post has time-constrained value. It is news, actions and blog posts."""
    draft = models.BooleanField(default=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, db_index=False)
    author = models.ForeignKey(auth.User, null=True, blank=True, on_delete=models.SET_NULL, db_index=False)
    description = models.TextField()
    punchline = models.TextField(blank=True, help_text="Punchline for social media. Defaults to description.")

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        unique_together = (('site', 'slug', 'lang'), )

    __str__ = lambda self: self.title

    def save(self, user=None, **kwargs):
        if user and not self.author:
            self.author = user
        super().save(user=user, **kwargs)

    def delete(self, **kwargs):
        self.site.get_engine().delete(self.site, post=self)
        self.site.get_deployer().delete(self.site, post=self)
        return super().delete(**kwargs)

    def get_url(self, absolute=False):
        return self.site.get_engine().get_post_url(self.site, self, absolute=absolute)


class Publish(models.Model):
    site = models.ForeignKey(Site, db_index=True, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, null=True, blank=True, db_index=False, on_delete=models.CASCADE)
    force = models.BooleanField(default=False, help_text="Upload all files no matter their modification time")
    purge = models.BooleanField(default=False, help_text="Clear all files in the bucket prior uploading")
    started = models.DateTimeField(auto_now_add=True, db_index=True)
    finished = models.DateTimeField(null=True)
    success =  models.BooleanField(null=True)
    message = models.CharField(max_length=512)

    objects = PublishManager()

    class Meta:
        verbose_name = _("Publish")
        verbose_name_plural = _("Publish")
        ordering = ("site", "-finished")

    @classmethod
    def is_running(cls, site: str):
        return Publish.objects.filter(
            site=site,
            started__gt=datetime.utcnow()-timedelta(minutes=1),
            finished=None).exists()

    def run(self):
        try:
            self.site.get_engine().render(self.site, post=self.post, force=self.force, purge=self.purge)
            self.site.get_deployer().deploy(self.site, post=self.post, force=self.force, purge=self.purge)
            # self.site.get_publishers().publish()
            self.success = True
        except Exception as e:
            self.message = str(e)
            self.success = False
            import traceback
            traceback.print_exception(e)
        finally:
            self.finished = datetime.utcnow()
            self.save()

    def clean(self):
        if not self.id:  # new record
            if Publish.is_running(self.site):
                raise ValidationError("Publish is already running")

    def save(self, **kwargs):
        if not self.finished:
            threading.Thread(target=self.run, daemon=True).start()
        return super().save(**kwargs)

