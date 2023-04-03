import pelican
import io
import threading

from datetime import datetime
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from pathlib import Path

from velican2.core import models as core
from velican2.pelican import logger


class App(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.pelican'

    def ready(self):
        post_save.connect(on_post_save, sender=core.Post)
        post_save.connect(on_page_save, sender=core.Page)
        post_save.connect(on_site_save, sender=core.Site)
        post_save.connect(on_publish_save, sender=core.Publish)


def on_post_save(instance: core.Post, **kwargs):
    dir = as_conf(instance.site)['CONTENT_DIR'] / "articles" / instance.slug
    dir.mkdir(exist_ok=True)
    with Path(dir / "index.md").open("wt") as file:
        write_post(instance, file)


def on_page_save(instance: core.Page, **kwargs):
    dir = as_conf(instance.site)['CONTENT_DIR'] / "pages"
    dir.mkdir(exist_ok=True)
    with Path(dir / (instance.slug + ".md")).open("wt") as file:
        write_page(instance, file)


def on_site_save(instance: core.Site, **kwargs):
    conf = as_conf(instance)
    conf["CONTENT_DIR"].mkdir(exist_ok=True)
    conf["PUBLISH_DIR"].mkdir(exist_ok=True)
    conf["PREVIEW_DIR"].mkdir(exist_ok=True)
    return True


def on_publish_save(instance: core.Publish, **kwargs):
    if instance.site.engine != "pelican":
        return
    if not instance.finished:
        threading.Thread(
            target=publish, args=(instance, ), daemon=True).start()

def as_conf(site: core.Site):
    return {
        'SITEURL': site.domain,
        'SITENAME': site.title,
        'PATH': settings.PELICAN_CONTENT / site.domain,
        'PAGE_PATHS': ["pages", ],
        'ARTICLE_PATHS': ["articles", ],
        'STATIC_CREATE_LINKS': True,  #  create (sym)links to static files instead of copying them
        'STATIC_CHECK_IF_MODIFIED': True,
        'DELETE_OUTPUT_DIRECTORY': False,
        'CACHE_CONTENT': True, # cache generated files
        # 'LOAD_CONTENT_CACHE': True,
        'OUTPUT_DIR': settings.PELICAN_OUTPUT / site.domain,
        'PREVIEW_DIR': settings.PELICAN_OUTPUT / site.domain / "preview",
    }


def publish(instance: core.Publish):
    try:
        proc = pelican.Pelican(as_conf(instance.site))
        proc.run()
        instance.success = True
    except Exception as e:
        instance.success = False
        instance.message = str(e)
    finally:
        instance.finished = datetime.now()
        instance.save()


def write_post(post: core.Post, writer: io.Writer):
    writer.write("title: "); writer.write(post.title); writer.write("\n")
    writer.write("created: "); writer.write(str(post.created)); writer.write("\n")
    writer.write("updated: "); writer.write(str(post.updated)); writer.write("\n")
    writer.write("author: "); writer.write(str(post.author)); writer.write("\n")
    writer.write("description: "); writer.write(post.description.replace("\n", "")); writer.write("\n")
    writer.write("\n")
    writer.write(post.content)


def write_page(page: core.Page, writer: io.Writer):
    writer.write(page.content)
