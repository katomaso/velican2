import pelican
 
from datetime import datetime
from functools import cached_property
from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _
from velican2.core import models as core

class Theme(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    path = models.CharField(max_length=256)

    class Meta:
        verbose_name = _("Theme")
        verbose_name_plural = _("Themes")


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


