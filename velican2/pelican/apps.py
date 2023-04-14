import io
import threading

from datetime import datetime
from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from pathlib import Path
from pelican.tools import pelican_themes

from velican2.pelican import logger


class App(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.pelican'

    def ready(self):
        if not settings.PELICAN_THEMES.is_dir():
            settings.PELICAN_THEMES.mkdir(exist_ok=True)

        # prefill Themes tables with builtin themes (into Pelican)
        if "migrat" not in settings.SUBCOMMAND:
            Theme = self.get_model("Theme")
            for (theme, _) in pelican_themes.themes():
                Theme.objects.get_or_create(name=Path(theme).parts[-1], defaults={
                    "installed": True,
                    "updated": datetime.now(),
                })

        post_save.connect(on_site_save, sender=apps.get_model("core", "Site"))
        post_save.connect(on_post_save, sender=apps.get_model("core", "Post"))
        post_save.connect(on_page_save, sender=apps.get_model("core", "Page"))
        post_save.connect(on_publish_save, sender=apps.get_model("core", "Publish"))


def on_site_save(instance, **kwargs): # instance: core.Site
    from velican2.pelican.models import Engine, Theme
    if instance.engine != "pelican":
        return
    _, created = Engine.objects.get_or_create(
        site=instance,
        defaults=dict(
            theme=Theme.objects.all().first(),
            post_url_template=Engine.POST_URL_TEMPLATES[0][1],
        )
    )
    if created:
        logger.info(f"Created default pelican engine for {instance.domain}")

def on_post_save(instance, **kwargs): # instance: core.Post
    from velican2.pelican.models import Engine
    if instance.site.engine != "pelican":
        return
    pelican = Engine.objects.get(site=instance.site)
    with pelican.get_post_path(instance).open("wt") as file:
        write_post(instance, file)


def on_page_save(instance, **kwargs): # instance: core.Page
    from velican2.pelican.models import Engine
    if instance.site.engine != "pelican":
        return
    pelican = Engine.objects.get(site=instance.site)
    with pelican.get_page_path(instance).open("wt") as file:
        write_page(instance, file)


def on_publish_save(instance, **kwargs): # instance: core.Publish
    from velican2.pelican.models import Engine
    if instance.site.engine != "pelican":
        return
    pelican = Engine.objects.get(site=instance.site)
    if not instance.finished:
        threading.Thread(
            target=lambda instance: pelican.publish(instance), args=(instance, ), daemon=True).start()


def write_post(post, writer: io.TextIOBase): # post: core.Post
    writer.write("title: "); writer.write(post.title); writer.write("\n")
    writer.write("created: "); writer.write(str(post.created)); writer.write("\n")
    writer.write("updated: "); writer.write(str(post.updated)); writer.write("\n")
    writer.write("author: "); writer.write(str(post.author)); writer.write("\n")
    writer.write("description: "); writer.write(post.description.replace("\n", "")); writer.write("\n")
    writer.write("\n")
    writer.write(post.content)


def write_page(page, writer: io.TextIOBase):  # page: core.Page
    writer.write(page.content)
