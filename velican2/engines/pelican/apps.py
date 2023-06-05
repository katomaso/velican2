import io
import pelican
import shutil

from datetime import datetime
from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from pathlib import Path
from pelican.tools import pelican_themes

from velican2.engines.pelican import logger


class Engine(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.engines.pelican'

    def ready(self):
        if not settings.PELICAN_THEMES.is_dir():
            settings.PELICAN_THEMES.mkdir(exist_ok=True)

        # prefill Themes tables with builtin themes (into Pelican)
        if "migrat" not in settings.SUBCOMMAND:
            Theme = self.get_model("Theme")
            for (theme, _) in pelican_themes.themes():
                logger.info(f"Found {theme} with pelican_themes - installing")
                Theme.objects.get_or_create(name=Path(theme).parts[-1], defaults={
                    "updated": datetime.now(),
                })
            Plugin = self.get_model("Plugin")
            for plugin in pelican.load_plugins(settings.PELICAN_DEFAULT_SETTINGS):
                logger.info(f"Found {plugin} with pelican.load_plugins() - installing")
                Plugin.objects.get_or_create(id=pelican.get_plugin_name(plugin))

        post_save.connect(on_site_save, sender=apps.get_model("core", "Site"))
        post_save.connect(on_post_save, sender=apps.get_model("core", "Post"))
        post_save.connect(on_page_save, sender=apps.get_model("core", "Page"))

    def _get_settings(self, site):
        Settings = self.get_model("Settings")
        return Settings.objects.get(site=site)

    def render(self, site, post=None, page=None, **kwargs):
        """Produce a HTML output from the database. This might update /index.html and other files."""
        settings = self._get_settings(site)
        if kwargs.get("purge", False):
            shutil.rmtree(settings.get_output_path())
        proc = pelican.Pelican(settings.conf)
        proc.run()

    def delete(self, site, post=None, page=None):
        """Delete source and rendered instances of post/page."""
        settings = self._get_settings(site)
        if post is not None:
            logger.info("Deleting {post.site}/{post}")
            settings.get_post_source_path(post).unlink()
            settings.get_post_output_path(post).unlink()
            return
        if page is not None:
            logger.info("Deleting {page.site}/{page}")
            settings.get_page_source_path(page).unlink()
            settings.get_page_output_path(page).unlink()
            return
        shutil.rmtree(settings.get_output_path())

    def get_output_path(self, site):
        """Get the path where rendered HTML files are written."""
        settings = self._get_settings(site)
        return settings.get_output_path()

    def get_output_page_path(self, site, page):
        """Get the path to given page."""
        settings = self._get_settings(site)
        return settings.get_page_output_path(page)

    def get_output_post_path(self, site, post):
        """Get the path to given post."""
        settings = self._get_settings(site)
        return settings.get_post_output_path(post)

    def get_page_url(self, site, page, absolute=True):
        settings = self._get_settings(site)
        url = settings.get_page_url(page)
        if absolute:
            return site.absolutize(url)
        return url

    def get_post_url(self, site, post, absolute=True):
        settings = self._get_settings(site)
        url = settings.get_post_url(post)
        if absolute:
            return site.absolutize(url)
        return url


def on_site_save(instance, **kwargs): # instance: core.Site
    from velican2.engines.pelican.models import Settings, Theme
    if instance.engine != "pelican":
        return
    _, created = Settings.objects.get_or_create(
        site=instance,
        defaults=dict(
            theme=Theme.objects.all().first(),
            post_url_template=Settings.POST_URL_TEMPLATES[0][1],
        )
    )
    if created:
        logger.info(f"Created default pelican engine for {instance.domain}")


def on_post_save(instance, **kwargs): # instance: core.Post
    from velican2.engines.pelican.models import Settings
    if instance.site.engine != "pelican":
        return
    pelican = Settings.objects.get(site=instance.site)
    logger.info(f"Writing file {pelican.get_post_source_path(instance)}")
    with pelican.get_post_source_path(instance).open("wt") as file:
        write_post(instance, file)


def on_page_save(instance, **kwargs): # instance: core.Page
    from velican2.engines.pelican.models import Settings
    if instance.site.engine != "pelican":
        return
    pelican = Settings.objects.get(site=instance.site)
    with pelican.get_page_source_path(instance).open("wt") as file:
        write_page(instance, file)


def write_post(post, writer: io.TextIOBase): # post: core.Post
    writer.write("Title: "); writer.write(post.title); writer.write("\n")
    writer.write("Date: "); writer.write(str(post.created)); writer.write("\n")
    if post.draft:
        writer.write("Status: draft\n")
    writer.write("Modified: "); writer.write(str(post.updated)); writer.write("\n")
    writer.write("Slug: "); writer.write(str(post.slug)); writer.write("\n")
    # writer.write("Tags: "); writer.write(str(post.created)); writer.write("\n")
    writer.write("Authors: "); writer.write(str(post.author)); writer.write("\n")
    if post.category:
        writer.write("Category: "); writer.write(str(post.category)); writer.write("\n")
    writer.write("Summary: "); writer.write(post.description.replace("\n", "")); writer.write("\n")
    writer.write("\n")
    writer.write(post.content)


def write_page(page, writer: io.TextIOBase):  # page: core.Page
    writer.write(page.content)
