import subprocess
from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from . import logger
from pathlib import Path
from velican2.core import models as core


class Settings(models.Model):
    site = models.ForeignKey(core.Site, on_delete=models.CASCADE)
    repository = models.CharField(max_length=256, help_text=_("Git repository for exporting sources for articles"))
    username = models.CharField(max_length=52)
    password = models.CharField(max_length=256, help_text=_("Password or token with write permissions for the repository"))

    def export(self, post=None, page=None):
        self.ensure_repository()
        engine = self.site.get_engine()
        path = None
        if post is not None:
            path = engine.get_page_source_path(page)
        elif page is not None:
            path = engine.get_post_source_path(post)
        else:
            logger.warn("Exporter needs a post or a page")
        updated_file = self.copy_file(engine.get_source_path(), path)
        self.sync(updated_file)

    def get_export_path(self):
        return settings.GIT_REPO_DIR / self.site.as_dirname()

    def ensure_repository(self):
        path = self.get_export_path()
        if not path.exists():
            try:
                subprocess.call(["git", "clone", self.repository, path.name], cwd=path.parent)
            except Exception as e:
                logger.error(e)
                path.mkdir()
                subprocess.call(["git", "init"], cwd=path)
                subprocess.call(["git", "remote", "add", "main", self.repository], cwd=path)
        return subprocess.call(["git", "status"], cwd=path) == 0

    def copy_file(self, source_dir: Path, source_path: Path):
        final_path = self.get_export_path() / source_dir.relative_to(source_path)
        logger.info(f"Copying file {final_path}")
        if not final_path.parent.exists():
            final_path.parent.mkdir()
        source_path.copy(final_path)
        return final_path

    def sync(self, path):
        repo_path = self.get_export_path()
        subprocess.call(["git", "add", repo_path.relative_to(path)], cwd=repo_path)
        subprocess.call(["git", "commit", "-m", "Update " + path.name], cwd=repo_path)
        subprocess.call(["git", "push", "origin", "main"], cwd=repo_path)


