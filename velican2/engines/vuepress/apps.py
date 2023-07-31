import subprocess

from django.apps import AppConfig


class VeupressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veupress'

    def render(self, site, post=None, page=None):
        settings = self._settings(site)
        subprocess.call(("yarn", "create", "vuepress-site", settings.get_source_path()))