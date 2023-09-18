import io
import pelican
import shutil

from django.apps import apps, AppConfig
from django.db.models.signals import post_save
from django.urls import reverse
from pathlib import Path

from velican2.engines.pelican import logger


class Engine(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.engines.pelican'

    def ready(self):
        post_save.connect(on_site_save, sender=apps.get_model("core", "Site"))
        post_save.connect(on_post_save, sender=apps.get_model("core", "Post"))
        post_save.connect(on_page_save, sender=apps.get_model("core", "Page"))

    def _get_settings(self, site):
        try:
            Settings = self.get_model("Settings")
            return Settings.objects.get(site=site)
        except Settings.DoesNotExist:
            object = Settings(site=site)
            object.save()
            return object

    def render(self, site, post=None, page=None, **kwargs):
        """Produce a HTML output from the database. This might update /index.html and other files."""
        settings = self._get_settings(site)
        if kwargs.get("force", False) and not (post or page):
            # regenerate all content
            for post in site.posts:
                write_post(settings, post)
            for page in site.pages:
                write_page(settings, page)
        if kwargs.get("purge", False):
            # remove all (stale) output
            shutil.rmtree(settings.get_output_path())
        if post is not None:
            write_post(settings, post)
        if page is not None:
            write_page(settings, page)
        settings.get_output_path().mkdir(exist_ok=True)
        if site.logo:
            logo_output_path = settings.get_output_path() / Path(site.logo.name).name
            if not logo_output_path.exists():
                shutil.copy2(site.logo.path, logo_output_path)
        proc = pelican.Pelican(settings.conf)
        proc.run()

    def delete(self, site, post=None, page=None):
        """Delete source and rendered instances of post/page."""
        settings = self._get_settings(site)
        if post is not None:
            logger.info("Deleting {post.site}/{post}")
            settings.get_post_source_path(post).unlink()
            settings.get_post_output_path(post).unlink()
            return
        if page is not None:
            logger.info("Deleting {page.site}/{page}")
            settings.get_page_source_path(page).unlink()
            settings.get_page_output_path(page).unlink()
            return
        shutil.rmtree(settings.get_output_path())

    def get_output_path(self, site):
        """Get the path where rendered HTML files are written."""
        settings = self._get_settings(site)
        return settings.get_output_path()

    def get_output_page_path(self, site, page):
        """Get the path to given page."""
        settings = self._get_settings(site)
        return settings.get_page_output_path(page)

    def get_output_post_path(self, site, post):
        """Get the path to given post."""
        settings = self._get_settings(site)
        return settings.get_post_output_path(post)

    def get_settings_url(self, site) -> str:
        settings = self._get_settings(site)
        return reverse("pelican:setting", kwargs={'site': site.urn})

    def get_page_url(self, site, page, absolute=True):
        settings = self._get_settings(site)
        url = settings.get_page_url(page)
        if absolute:
            return site.absolutize(url)
        return url

    def get_post_url(self, site, post, absolute=True):
        settings = self._get_settings(site)
        url = settings.get_post_url(post)
        if absolute:
            return site.absolutize(url)
        return url


def on_site_save(instance, **kwargs): # instance: core.Site
    from velican2.engines.pelican.models import Settings, Theme
    if instance.engine != "pelican":
        return
    _, created = Settings.objects.get_or_create(
        site=instance,
        defaults=dict(
            theme=Theme.objects.all().first(),
        )
    )
    if created:
        logger.info(f"Created default pelican engine for {instance}")


def on_post_save(instance, **kwargs): # instance: core.Post
    from velican2.engines.pelican.models import Settings
    if instance.site.engine != "pelican":
        return
    pelican = Settings.objects.get(site=instance.site)
    write_post(pelican, instance)


def write_post(pelican, post):
    logger.info(f"Writing post {pelican.get_post_source_path(post)}")
    with pelican.get_post_source_path(post).open("wt") as file:
        write_post_content(post, file)
    if post.heading:
        shutil.copy2(post.heading.path, pelican.get_post_output_path(post).with_suffix(Path(post.heading.path).suffix))


def on_page_save(instance, **kwargs): # instance: core.Page
    from velican2.engines.pelican.models import Settings
    if instance.site.engine != "pelican":
        return
    pelican = Settings.objects.get(site=instance.site)
    write_page(pelican, instance)


def write_page(pelican, page):
    logger.info(f"Writing page {pelican.get_page_source_path(page)}")
    with pelican.get_page_source_path(page).open("wt") as file:
        write_page_content(page, file)
    if page.heading:
        shutil.copy2(page.heading.path, pelican.get_page_output_path(page).with_suffix(Path(page.heading.path).suffix))


def write_post_content(post, writer: io.TextIOBase): # post: core.Post
    metadata = {
        "Title": post.title,
        "Date": str(post.created),
        "Author": str(post.author),
        "Modified": str(post.updated),
        "Slug": post.slug,
        "Oid": str(post.id),  # original article ID
        "Summary": post.description.replace("\n", "")
    }

    if post.translation_of:
        metadata["Translation"] = "true"
        metadata["Oid"] = str(post.translation_of.id)
    if post.heading:
        metadata["Heading"] = post.heading.name
    if post.draft:
        metadata["Status"] = "draft"
    if post.lang:
        metadata["Lang"] = post.lang
    if post.category:
        metadata["Category"] = str(post.category)
    # writer.write("Tags: "); writer.write(str(post.created)); writer.write("\n")

    for key, value in metadata.items:
        writer.write(key); writer.write(": "); writer.write(value); writer.write("\n")
    writer.write("\n")
    writer.write(post.content)


def write_page_content(page, writer: io.TextIOBase):  # page: core.Page
    writer.write("Title: "); writer.write(page.title); writer.write("\n")
    writer.write("Date: "); writer.write(str(page.created)); writer.write("\n")
    writer.write("Modified: "); writer.write(str(page.updated)); writer.write("\n")
    if page.heading:
        writer.write("Heading: "), writer.write(page.heading.name); writer.write("\n")
    if page.lang:
        writer.write("Lang: "); writer.write(page.lang); writer.write("\n")
    writer.write("\n")
    writer.write(page.content)
