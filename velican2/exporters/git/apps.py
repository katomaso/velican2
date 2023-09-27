from django.apps import apps, AppConfig
from django.conf import settings

class GitExporterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.exporters.git'

    def ready(self):
        settings.GIT_REPO_DIR.mkdir(exist_ok=True, parents=True)

    def export(self, site, post=None, page=None):
        settings = apps.get_model("git.Settings").objects.filter(site=site).first()
        if not self.settings:
            return
        return settings.export(post=post, page=page)

