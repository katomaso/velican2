import subprocess
import shutil

from datetime import datetime
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
    last_sync = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=256, null=True, blank=True)

    def clean(self) -> None:
        if self.repository.startswith("git@"):
            raise models.ValidationError("Only HTTPS repositories are supported")
        return super().clean()

    def save(self, **kwargs) -> None:
        if self.repository.startswith("https://"):
            self.repository = self.repository[len("https://"):]
        return super().save(**kwargs)

    def export(self, post=None, page=None):
        engine = self.site.get_engine()
        path = None
        if page is not None:
            path = engine.get_page_source_path(page)
        elif post is not None:
            path = engine.get_post_source_path(post)
        else:
            logger.warn("Exporter needs a post or a page")
        try:
            self.ensure_repository()
            updated_file = self.copy_file(engine.get_source_path(self.site), path)
            return self.sync(updated_file)
        except Exception as e:
            self.error = str(e)
            self.last_sync = datetime.now()
            self.save()

    def get_repository_url(self):
        return f"https://{self.username}:{self.password}@{self.repository}"

    def get_export_path(self):
        return settings.GIT_REPO_DIR / self.site.as_dirname()

    def ensure_repository(self, rethrow=False):
        path = self.get_export_path()
        logger.debug(f"export path {path}")
        if not path.exists():
            if 0 != subprocess.call(["git", "clone", self.get_repository_url(), path.name], cwd=path.parent):
                path.mkdir()
                subprocess.call(["git", "init"], cwd=path)
                subprocess.call(["git", "remote", "add", "origin", self.get_repository_url()], cwd=path)
        return subprocess.call(["git", "status"], cwd=path) == 0

    def copy_file(self, source_dir: Path, source_path: Path):
        final_path = self.get_export_path() / source_path.relative_to(source_dir)
        logger.info(f"Copying file {final_path}")
        if not final_path.parent.exists():
            final_path.parent.mkdir()
        shutil.copy(source_path, final_path)
        return final_path

    def sync(self, path):
        repo_path = self.get_export_path()
        if any((
            subprocess.call(["git", "add", path.relative_to(repo_path)], cwd=repo_path),
            subprocess.call(["git", "commit", "-m", "Update " + path.name], cwd=repo_path),
            subprocess.call(["git", "push", "-u", "origin", "main"], cwd=repo_path),
        )): # return value of 1 of any subprocess.call means failure
            self.error = "Failed to git sync"
        else:
            self.error = None
        self.last_sync = datetime.utcnow()
        self.save()
        return self.error is None


