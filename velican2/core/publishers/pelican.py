
from pathlib import Path
import pelican
import io

from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from velican2.core import models, logger

@receiver(post_save, sender=models.Post)
def on_post_save(instance: models.Post, **kwargs):
    dir = as_conf(instance.site)['CONTENT_DIR'] / "articles" / instance.slug
    dir.mkdir(exist_ok=True)
    with Path(dir / "index.md").open("wt") as file:
        write_post(instance, file)


@receiver(post_save, sender=models.Page)
def on_page_save(instance: models.Page, **kwargs):
    dir = as_conf(instance.site)['CONTENT_DIR'] / "pages"
    dir.mkdir(exist_ok=True)
    with Path(dir / (instance.slug + ".md")).open("wt") as file:
        write_page(instance, file)


@receiver(post_save, sender=models.Site)
def on_site_save(instance: models.Site, **kwargs):
    conf = as_conf(instance)
    conf["CONTENT_DIR"].mkdir(exist_ok=True)
    conf["PUBLISH_DIR"].mkdir(exist_ok=True)
    conf["PREVIEW_DIR"].mkdir(exist_ok=True)
    return True


def on_publish_save(instance: models.Publish, **kwargs):
    if instance.created or not instance.updated:
        logger.debug(f"Not reacting to Publish save because of created: {instance.created} or not updated: {instance.updated}")
        return
    publish(instance)


def as_conf(site: models.Site):
    return {
        'CONTENT_DIR': settings.PELICAN['CONTENT_ROOT'] / site.domain,
        'OUTPUT_DIR': settings.PELICAN['OUTPUT_ROOT'] / site.domain,
        'PREVIEW_DIR': settings.PELICAN['OUTPUT_ROOT'] / site.domain / "preview",
    }


async def publish(site: models.Site):
    try:
        proc = pelican.Pelican(as_conf(site))
        proc.run()
        publish.failed = False
    except Exception as e:
        publish.result = str(e)
        publish.failed = True
    finally:
        publish.save()


def write_post(post: models.Post, writer: io.Writer):
    writer.write("title: "); writer.write(post.title); writer.write("\n")
    writer.write("created: "); writer.write(str(post.created)); writer.write("\n")
    writer.write("updated: "); writer.write(str(post.updated)); writer.write("\n")
    writer.write("author: "); writer.write(str(post.author)); writer.write("\n")
    writer.write("description: "); writer.write(post.description.replace("\n", "")); writer.write("\n")
    writer.write("\n")
    writer.write(post.content)


def write_page(page: models.Page, writer: io.Writer):
    writer.write(page.content)
