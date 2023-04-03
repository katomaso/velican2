from django.db import models
from django.utils.translation import gettext as _
from velican2.core import models as core

class Theme(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    path = models.CharField(max_length=256)


class Pelican(models.Model):
    site = models.OneToOneField(core.Site, related_name="pelican", on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL)
    show_page_in_menu = models.BooleanField(default=True, null=False, help_text=_("Display pages in menu"))
    show_category_in_menu = models.BooleanField(default=True, null=False, help_text=_("Display categories in menu"))
    post_url = models.CharField(max_length=255, choices=(
        (f"{_('slug')}.html", '{date:%Y}/{date:%b}/{date:%d}/{slug}.html'),
        (f"{_('slug')}/index.html", '{slug}/index.html'),
        (f"{_('year')}/{_('slug')}.html", '{date:%Y}/{slug}.html'),
        (f"{_('year')}/{_('month')}/{_('slug')}.html", '{date:%Y}/{date:%b}/{slug}.html'),
        (f"{_('author')}/{_('slug')}.html", '{category}/{slug}.html')
        (f"{_('category')}/{_('slug')}.html", '{category}/{slug}.html'),
        (f"{_('category')}/{_('year')}/{_('slug')}.html", '{category}/{date:%Y}/{slug}.html')
    ))
    page_url_prefix = models.CharField(max_length=35, help_text=_("Pages URL prefix (pages urls will look like 'prefix/slug.html')"))
    facebook = models.CharField(max_length=128, null=True)
    twitter = models.CharField(max_length=128, null=True)
    linkedin = models.CharField(max_length=128, null=True)
    github = models.CharField(max_length=128, null=True)

    def get_page_url(self, site: core.Site, page: core.Page):
        if self.page_url_prefix:
            return site.domain + "/" + self.page_url_prefix + "/" + page.slug + ".html"
        return site.domain + "/" + page.slug + ".html"

    def get_post_url(self, site: core.Site, post: core.Post):
        return site.domain + "/" + self.post_url.format(
            slug=post.slug,
            date=post.created,
            category=post.category.slug if post.category else "",
            author=post.author.username if post.author else "",
            lang=post.lang,
        )
