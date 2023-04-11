import io
import pelican
import re
import subprocess

from pathlib import Path
from datetime import datetime
from functools import cached_property
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from django.utils.translation import gettext as _
from velican2.core import models as core
from velican2.pelican import logger
from pelican.tools import pelican_themes

#
# HACK: inject different err function so we can actually see errors
#
def pelican_themes_err(msg:str, die=None):
    raise RuntimeError(msg)
pelican_themes.err = pelican_themes_err


class ThemeSource(models.Model):
    """Git URL to the theme(s) that will be downloaded and if `not multiple` then installed automatically"""
    url = models.CharField(max_length=256, null=False, primary_key=True)
    multiple = models.BooleanField(default=False, help_text="Check when the repository contains multiple themes. You cannot install them easily then")
    updated = models.DateTimeField(null=True, blank=True)
    log = models.TextField(null=True)

    __str__ = lambda self: self.name

    @property
    def downloaded(self):
        return self.path.exists()

    @property
    def installed(self):
        return self.themes.count() > 0

    @property
    def name(self):
        return re.search(r'/([^/]+)\.git', self.url).group(1)

    @property
    def path(self):
        return settings.PELICAN_THEMES / self.name

    def download(self, save=True):
        if self.downloaded:
            return True
        proc = subprocess.Popen(
            ["git", "clone", "--recurse-submodules", self.url, self.name],
            cwd=settings.PELICAN_THEMES, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
        if proc.wait() == 0:
            self.updated = datetime.now()
            self.log = None
        else:
            self.log = proc.stdout.read()
            logger.debug(self.log)
        if save:
            self.save()
        return proc.poll() == 0

    def update(self, recurse=True, save=True):
        proc = subprocess.Popen(
            ["git", "pull",  "--recurse-submodules"],
            cwd=str(self.path), stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
        if proc.wait() == 0:
            self.updated = datetime.now()
            self.log = None
            if recurse:
                for theme in self.themes.all():
                    theme.update()
        else:
            self.log = proc.stdout.read()
            logger.debug(self.log)
        if save:
            return self.save()
        return self.poll() == 0

    def install(self):
        if self.multiple or self.installed:
            return None
        return Theme.objects.create(
            source=self,
        ).installed

    def clear(self, save=True):
        self.path.unlink()
        self.updated = None
        self.log = None
        if save:
            return self.save()

    def delete(self, **kwargs):
        self.clear()
        return super().delete(**kwargs)

    def save(self, **kwargs):
        if self.url.startswith("https") and not self.url.endswith(".git"):
            self.url += ".git"
        if not self.downloaded:
            self.download(save=False)
        if self.downloaded and not self.installed:
            self.install()
        return super().save(**kwargs)


def is_theme(path):
    return path.is_dir()


class Theme(models.Model):
    name = models.CharField(max_length=32, blank=True, primary_key=True, help_text="Must be set explicitely for Multi Theme Source")
    mapping = models.TextField(help_text="Jinja code to define necessary variables for the theme")
    installed = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now_add=True)
    log = models.TextField(null=True)
    source = models.ForeignKey(ThemeSource, on_delete=models.SET_NULL, null=True, related_name="themes")

    class Meta:
        verbose_name = _("Theme")
        verbose_name_plural = _("Themes")

    @property
    def screenshots_jpeg(self):
        return [io.FileIO(path, mode='r', closefd=True)
                for path in Path(self.path).iterdir()
                if str(path).endswith("jpg") or str(path).endswith("jpeg")]

    @property
    def screenshots_png(self):
        return [io.FileIO(path, mode='r', closefd=True)
                for path in self.path.iterdir()
                if str(path).endswith("png")]

    @property
    def path(self):
        if not self.source:
            raise RuntimeError("Builtin themes have no path")
        if self.source.multiple:
            return self.source.path / self.name
        return self.source.path

    __str__ = lambda self: self.name

    def update(self, save=True):
        if not self.installed:
            return
        try:
            pelican_themes.install(str(self.path), u=True, v=False)
            self.updated = datetime.now()
        except Exception as e:
            self.log = str(e)
        if save:
            self.save()

    def install(self, save=True):
        if self.installed:
            return
        try:
            pelican_themes.install(str(self.path), v=False)
            self.installed = True
        except Exception as e:
            self.log = str(e)
        if save:
            self.save()

    def delete(self, **kwargs):
        if not self.installed:
            return
        try:
            pelican_themes.remove(self.name, v=False)
            self.installed = False
        except Exception as e:
            self.log = str(e)
        return super().delete(**kwargs)

    def save(self, **kwargs):
        if not self.name:
            self.name = self.source.name
        if self.source and not is_theme(self.path):
            raise ValidationError(str(self.path) + " is not a theme directory")
        self.install(save=False)
        return super().save(**kwargs)


class Settings(models.Model):
    site = models.OneToOneField(core.Site, related_name="pelican", on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.DO_NOTHING)
    show_page_in_menu = models.BooleanField(default=True, null=False, help_text=_("Display pages in menu"))
    show_category_in_menu = models.BooleanField(default=True, null=False, help_text=_("Display categories in menu"))
    post_url_template = models.CharField(max_length=255, choices=(
        (f"{_('slug')}.html", '{date:%Y}/{date:%b}/{date:%d}/{slug}.html'),
        (f"{_('slug')}/index.html", '{slug}/index.html'),
        (f"{_('year')}/{_('slug')}.html", '{date:%Y}/{slug}.html'),
        (f"{_('year')}/{_('month')}/{_('slug')}.html", '{date:%Y}/{date:%b}/{slug}.html'),
        (f"{_('author')}/{_('slug')}.html", '{category}/{slug}.html'),
        (f"{_('category')}/{_('slug')}.html", '{category}/{slug}.html'),
        (f"{_('category')}/{_('year')}/{_('slug')}.html", '{category}/{date:%Y}/{slug}.html'),
    ))
    page_url_prefix = models.CharField(max_length=35, help_text=_("Pages URL prefix (pages urls will look like 'prefix/{slug}.html')"))
    category_url_prefix = models.CharField(max_length=35, help_text=_("Category URL prefix (pages urls will look like 'prefix/{slug}.html')"))
    author_url_prefix = models.CharField(max_length=35, help_text=_("Author URL prefix (pages urls will look like 'prefix/{slug}.html')"))
    facebook = models.CharField(max_length=128, null=True)
    twitter = models.CharField(max_length=128, null=True)
    linkedin = models.CharField(max_length=128, null=True)
    github = models.CharField(max_length=128, null=True)

    class Meta:
        verbose_name = _("Settings")
        verbose_name_plural = _("Settings")

    @property
    def page_url_template(self):
        return (self.page_url_prefix + "/" if self.page_url_prefix else "") + "{slug}.html"

    @property
    def category_url_template(self):
        return (self.category_url_prefix + "/" if self.category_url_prefix else "") + "{slug}.html"

    @property
    def author_url_template(self):
        return (self.author_url_prefix + "/" if self.author_url_prefix else "") + "{slug}.html"

    def save(self, **kwargs):
        conf = self.as_conf()
        conf["PATH"].mkdir(exist_ok=True)
        (conf["PATH"] / conf['PAGE_PATHS'][0]).mkdir(exist_ok=True)
        (conf["PATH"] / conf['ARTICLE_PATHS'][0]).mkdir(exist_ok=True)
        conf["OUTPUT_DIR"].mkdir(exist_ok=True)
        conf["PREVIEW_DIR"].mkdir(exist_ok=True)
        return super().save(**kwargs)

    @cached_property
    def as_conf(self):
        return {
            'SITEURL': self.site.domain,
            'SITENAME': self.site.title,
            'PATH': settings.PELICAN_CONTENT / self.site.domain / self.site.path,
            'PAGE_PATHS': ["pages", ],
            'ARTICLE_PATHS': ["articles", ],
            'STATIC_PATHS': ['images', ],
            'STATIC_CREATE_LINKS': True,  #  create (sym)links to static files instead of copying them
            'STATIC_CHECK_IF_MODIFIED': True,
            'DELETE_OUTPUT_DIRECTORY': False,
            'CACHE_CONTENT': True, # cache generated files
            # 'LOAD_CONTENT_CACHE': True,
            'ARTICLE_URL': self.post_url_template if not self.post_url_template.endswith("index.html") else self.post_url_template[:-10],
            'ARTICLE_SAVE_AS': self.post_url_template,
            'PAGE_URL': self.page_url_template,
            'PAGE_SAVE_AS': self.page_url_template,
            'CATEGORY_URL': self.category_url_template,
            'CATEGORY_SAVE_AS': self.category_url_template,
            'AUTHOR_URL': self.author_url_template,
            'AUTHOR_SAVE_AS': self.author_url_template,
            'OUTPUT_DIR': settings.PELICAN_OUTPUT / self.site.domain / self.site.path,
            'PREVIEW_DIR': settings.PELICAN_OUTPUT / self.site.domain / self.site.path / "preview",
        }

    def get_page_path(self, page: core.Page):
        return self.as_conf()['PATH'] / self.as_conf()['PAGE_PATHS'][0] / page.slug + ".md"

    def get_post_path(self, post: core.Post):
        return self.as_conf()['PATH'] / self.as_conf()['ARTICLE_PATHS'][0] / post.slug + ".md"

    def get_page_url(self, site: core.Site, page: core.Page):
        return site.absolutize(
            self.post_url_template.format(
                slug=page.slug
            ))

    def get_post_url(self, site: core.Site, post: core.Post):
        return site.absolutize(
            self.post_url_template.format(
                slug=post.slug,
                date=post.created,
                category=post.category.slug if post.category else "",
                author=post.author.username if post.author else "",
                lang=post.lang,
            ))
    
    def publish(self, publish: core.Publish):
        try:
            proc = pelican.Pelican(self.as_conf())
            proc.run()
            publish.success = True
        except Exception as e:
            publish.success = False
            publish.message = str(e)
        finally:
            publish.finished = datetime.now()
            publish.save()


