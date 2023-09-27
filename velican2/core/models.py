import threading

from pathlib import Path

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from django.db import models
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
from django.core.validators import validate_unicode_slug, RegexValidator
from django.utils.translation import gettext as _
from django.utils.text import slugify

from velican2 import engines
from velican2 import deployers

from .managers import PublishManager
from . import logger

class UpdateException(Exception):
    pass

LANG_CHOICES = (
    ("cs", "cs"),
    ("en", "en"),
)


def site_logo_upload(site, filename):
    return Path(settings.MEDIA_ROOT / site.urn / filename).with_stem("logo")

def site_heading_upload(site, filename):
    return Path(settings.MEDIA_ROOT / site.urn / filename).with_stem("heading")

ENGINE_CHOICES = tuple((engine, engine.title()) for engine in engines.engines)
DEPLOYER_CHOICES = (
    ("caddy", "local web server"),
    ("aws", "AWS CloudFront"),
)

class Site(models.Model):
    urn = models.CharField(max_length=128, db_index=True, help_text="Example: example.com/blog", unique=True,
                           validators=(RegexValidator(regex=r'^([a-zA-Z0-9_\-][a-zA-Z0-9_/\-]+\.?)+$'),
                                       RegexValidator(regex=r'[^\./]$', message=_("URN must not end with dot or slash"))))
    admin = models.ForeignKey(auth.User, on_delete=models.CASCADE, related_name="+")
    staff = models.ManyToManyField(auth.User, blank=True)
    lang = models.CharField(max_length=2, choices=LANG_CHOICES, default=settings.LANGUAGE_CODE[0:2])
    timezone = models.CharField(max_length=128, default=settings.TIME_ZONE)
    secure = models.BooleanField(default=True, help_text="The site is served via secured connection https")

    title = models.CharField(max_length=128)
    subtitle = models.TextField(null=True)
    logo = models.ImageField(blank=True, null=True, upload_to=site_logo_upload)
    heading = models.ImageField(blank=True, null=True, upload_to=site_heading_upload)

    allow_crawlers = models.BooleanField(default=True, help_text="Allow search engines to index this page")
    allow_training = models.BooleanField(default=True, help_text="Allow AI engines to index this page")

    engine = models.CharField(max_length=12, null=False, choices=ENGINE_CHOICES, default=engines.engines[0])
    deployment = models.CharField(max_length=12, null=False, choices=DEPLOYER_CHOICES, default=DEPLOYER_CHOICES[0][0])

    facebook = models.CharField(max_length=128, null=True, blank=True)
    twitter = models.CharField(max_length=128, null=True, blank=True)
    linkedin = models.CharField(max_length=128, null=True, blank=True)
    github = models.CharField(max_length=128, null=True, blank=True)
    instagram = models.CharField(max_length=128, null=True, blank=True)
    fediverse = models.CharField(max_length=128, null=True, blank=True)

    # publish_to_facebook = models.BooleanField(default=False)
    # publish_to_instagram = models.BooleanField(default=False)
    # publish_to_twitter = models.BooleanField(default=False)
    # publish_to_linkedin = models.BooleanField(default=False)
    # publish_to_fediverse = models.BooleanField(default=False)

    webmentions = models.BooleanField(default=False, help_text="Should your site use webmentions")
    webmentions_external = models.CharField(max_length=256, blank=True, null=True, help_text="URL of an external webmentions service (optional). Leave empty for the builtin service.")

    matomo = models.BooleanField(default=False, help_text="Should your site use usage-tracking service")
    matomo_external = models.CharField(max_length=256, null=True, blank=True, help_text=_("URL of an usage-tracking service"))
    matomo_external_id = models.CharField(max_length=64, null=True, blank=True, help_text="SITE_ID for the external tracking service")

    # google_adsense = 
    google_analytics_code = models.CharField(max_length=64, null=True, blank=True, help_text="Your google analytics code UA-XYZ")

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")

    __str__ = lambda self: self.urn

    @property
    def posts(self):
        return Post.objects.all().filter(site=self)

    @property
    def pages(self):
        return Page.objects.all().filter(site=self)

    def as_dirname(self):
        return self.urn.replace("/", "#")

    def get_engine(self):
        return engines.get_engine(self.engine)

    def get_engine_url(self) -> str:
        return self.get_engine().get_settings_url(self)

    def get_deployer(self):
        return deployers.get_deployer(self.deployment)

    def publish(self, user: auth.User, **kwargs):
        return Publish.get_running() or Publish.objects.create(
            site=self,
            user=user,
            **kwargs
        )

    def delete(self, **kwargs):
        self.get_engine().delete(site=self)
        self.get_deployer().delete(site=self)
        return super().delete(**kwargs)

    def absolutize(self, path):
        return ("https://" if self.secure else "http://") + self.urn + "/" + path

    def can_add_content(self, user: auth.User):
        return self.admin == user or self.staff.contains(user)

    def can_manage(self, user: auth.User):
        return self.admin == user

    def get_media_dir(self) -> Path:
        return settings.MEDIA_ROOT / self.urn


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
    return Path(settings.MEDIA_ROOT / content.site.urn / content.slug / filename).with_stem("heading")

class Content(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, validators=(validate_unicode_slug,))
    lang = models.CharField(max_length=5, choices=LANG_CHOICES)
    content = models.TextField()
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    heading = models.ImageField(blank=True, null=True, upload_to=content_heading_upload)
    updated_count = models.IntegerField(default=0, blank=True, help_text="How many times was the content updated")
    updated_words = models.IntegerField(default=0, blank=True, help_text="How many words were changed during its lifespan")

    __str__ = lambda self: self.title

    class Meta:
        abstract = True

    # For some unknown reason the prev.updated is always like 90 seconds ahead
    def clean(self):
        if self.pk: # model aready exists
            prev = self.__class__.objects.get(pk=self.pk)
            logger.debug(f"prev.updated {prev.updated} MUST BE <= {self.updated}")
            if prev.updated > self.updated:
                raise ValidationError("You are editing an outdated version")
        return super().clean()

    def can_edit(self, user: auth.User):
        return self.site.can_add_content(user)

    def save(self, user=None, **kwargs):
        if user and not self.can_edit(user):
            raise PermissionError("You don't have edit rights on this")
        if not self.created:
            self.updated = None
        if not self.id:
            self.updated_words = self.content.count(" ")
        else:
            self.updated_count += 1
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(**kwargs)


class Page(Content):
    """Page will appear in the top-menu of your main page (and other pages).
    It is static pages that has value through the whole tile such as "about-me" and "services".
    """
    class Meta:
        abstract = False
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        unique_together = (('site', 'slug', 'lang'), )

    def get_url(self, absolute=False):
        return self.site.get_engine().get_page_url(self.site, self, absolute=absolute)
    
    def delete(self, **kwargs):
        self.site.get_engine().delete(self.site, page=self)
        self.site.get_deployer().delete(self.site, page=self)
        return super().delete(**kwargs)

    def get_media_dir(self) -> Path:
        return self.site.get_media_dir / self.pk


class Post(Content):
    """Post has time-constrained value. It is news, actions and blog posts."""
    draft = models.BooleanField(default=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, db_index=False)
    author = models.ForeignKey(auth.User, null=True, blank=True, on_delete=models.SET_NULL, db_index=False)
    translation_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, db_index=False, related_name="translations")
    description = models.TextField()
    punchline = models.TextField(blank=True, help_text="Punchline for social media. Defaults to description.")
    broadcast = models.BooleanField(default=True, help_text="If the post should be published on all linked social media")

    class Meta:
        abstract = False
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

    def get_url(self, absolute=True):
        return self.site.get_engine().get_post_url(self.site, self, absolute=absolute)


def content_image_upload(self, filename):
    return Path(settings.MEDIA_ROOT / self.site.urn / (self.post.slug if self.post else self.slug) / (filename if not self.name else filename.with_stem(self.name)))

class Image(models.Model):
    """Images uploaded for the site. They will be sotred in MEDIA folder and most likely simply linked to the output directory."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, null=True, on_delete=models.SET_NULL)
    slug = models.CharField(max_length=64, help_text="Slug of matching content - must not change during its lifetime")
    name = models.CharField(max_length=32, null=True)
    image = models.ImageField(upload_to=content_image_upload)

    __str__ = lambda self: self.image.name

    def delete(self, **kwargs) -> Tuple[int, Dict[str, int]]:
        self.image.delete()
        Path(self.image.path).unlink()
        return super().delete(**kwargs)


class Publish(models.Model):
    """Publish task that will start engine's rendering and deploiyer's deploy functions."""
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


class SocialPublish(models.Model):
    class Meta:
        unique_together = ('post', 'network')

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    network = models.CharField(max_length=2, choices=(
        ("fb", "facebook"),
        ("ig", "instagram"),
        ("x", "twitter"),
        ("li", "linkedin"),
        ("fv", "fediverse"),
    ))
    published_at = models.DateField(auto_now_add=True)


class Mention(models.Model):
    """Metions on other articles/videos that the author wants to prevail for themself."""
    site = models.ForeignKey(Site, db_index=True, on_delete=models.CASCADE)
    url = models.CharField(max_length=256)
    comment = models.TextField(blank=True, null=True, help_text="Feel free to use markdown")
    rating = models.SmallIntegerField(help_text="Rating where -2 is completely disagree through neutral 0 to like at +2", choices=((-2, "-2"), (-1, "-1"), (0, "0"), (1, "1"), (2, "2")))
    tag = models.ForeignKey(Category, blank=True, null=True, on_delete=models.DO_NOTHING)

    __str__ = lambda self: f"{self.site} -> {self.url}"

    class Meta:
        verbose_name = _("Mention")
        verbose_name_plural = _("Mentions")