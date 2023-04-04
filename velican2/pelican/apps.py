import io
import threading

from datetime import datetime
from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from pathlib import Path


class App(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.pelican'

    def ready(self):
        post_save.connect(on_post_save, sender=apps.get_model("core", "Post"))
        post_save.connect(on_page_save, sender=apps.get_model("core", "Page"))
        post_save.connect(on_publish_save, sender=apps.get_model("core", "Publish"))


def on_post_save(instance, **kwargs): # instance: core.Post
    with instance.site.pelican.get_post_path(instance).open("wt") as file:
        write_post(instance, file)


def on_page_save(instance, **kwargs): # instance: core.Page
    with instance.site.pelican.get_page_path(instance).open("wt") as file:
        write_page(instance, file)


def on_publish_save(instance, **kwargs): # instance: core.Publish
    if instance.site.engine != "pelican":
        return
    if not instance.finished:
        threading.Thread(
            target=lambda instance: instance.site.pelican.publish(instance), args=(instance, ), daemon=True).start()


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
