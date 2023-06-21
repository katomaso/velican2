import pelican

from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from pelican.tools import pelican_themes
from velican2.engines.pelican import models, logger

class Command(BaseCommand):
    def handle(self, *args, **options):
        # prefill Themes tables with builtin themes (into Pelican)
        for (theme, _) in pelican_themes.themes():
            logger.info(f"Found {theme} with pelican_themes - installing")
            models.Theme.objects.get_or_create(name=Path(theme).parts[-1], defaults={
                "updated": datetime.now(),
            })
        for plugin in pelican.load_plugins(settings.PELICAN_DEFAULT_SETTINGS):
            logger.info(f"Found {plugin} with pelican.load_plugins() - installing")
            models.Plugin.objects.get_or_create(id=pelican.get_plugin_name(plugin))
