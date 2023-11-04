import threading

from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models.signals import post_save

from .. import IExporter

class GitExporterConfig(AppConfig, IExporter):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.exporters.git'

    def ready(self):
        settings.GIT_REPO_DIR.mkdir(exist_ok=True, parents=True)
        post_save.connect(on_post_save, sender=apps.get_model("core", "Post"))
        post_save.connect(on_page_save, sender=apps.get_model("core", "Page"))

    def is_available(self):
        return True

    def is_active(self, site):
        return apps.get_model("git.Settings").objects.filter(site=site).exists()
    
    def get_activate_form(self, site):
        pass  # TODO

    @classmethod
    def export(self, site, post=None, page=None):
        settings = apps.get_model("git.Settings").objects.filter(site=site).first()
        if not settings:
            return False
        return settings.export(post=post, page=page)


def on_post_save(instance, **kwargs): # instance: core.Post
    threading.Thread(target=GitExporterConfig.export,
                     args=(instance.site, ), kwargs={'post': instance},
                     daemon=True).start()

def on_page_save(instance, **kwargs): # instance: core.Page
    threading.Thread(target=GitExporterConfig.export,
                    args=(instance.site, ), kwargs={'page': instance},
                    daemon=True).start()
