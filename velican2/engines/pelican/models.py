import io
import toml
import pelican
import pelican.paginator
import shutil
import subprocess
import urllib
import zipfile

from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models

from django.utils.translation import gettext as _
from velican2.core import models as core
from velican2.engines.pelican import logger
from pelican.tools import pelican_themes
#
# HACK: inject different err function so we can actually see errors
#
def pelican_themes_err(msg:str, die=None):
    raise RuntimeError(msg)
pelican_themes.err = pelican_themes_err

def theme_upload_to(instance, filename):
    return f"themes/{instance.name}/{Path(filename).name}"

class Theme(models.Model):
    """Git URL to the theme(s) that will be downloaded and if `not multiple` then installed automatically"""
    name = models.CharField(max_length=32, blank=True, primary_key=True, help_text="Must be set explicitely for cloning a repo under different name")
    url = models.CharField(max_length=256, null=False)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to=theme_upload_to)
    image1 = models.ImageField(blank=True, null=True, upload_to=theme_upload_to)
    image2 = models.ImageField(blank=True, null=True, upload_to=theme_upload_to)
    theme_settings = models.TextField(blank=True, null=True, help_text="Define extra variables for the theme (using KEY = 'value' or KEY = conf.EXISTING_KEY)")
    user_settings = models.TextField(blank=True, null=True, help_text="Define extra variables for the theme (using toml syntax: KEY = 'value'")
    updated = models.DateTimeField(null=True, blank=True)
    log = models.TextField(null=True)

    __str__ = lambda self: self.name

    @property
    def downloaded(self):
        return self.path.exists()

    @property
    def installed(self):
        if not self.name:
            return False
        return self.name in [Path(path).stem for path, _ in pelican_themes.themes()]

    @property
    def path(self):
        return settings.PELICAN_THEMES / self.name

    def download(self, save=True):
        """Download theme from given URL to settings.PELICAN_THEMES path"""
        if self.url.endswith(".zip"):
            zip_path = self.path.with_suffix(".zip")
            urllib.request.urlretrieve(self.url, zip_path)
            z = zipfile.ZipFile(zip_path)
            l = z.infolist()
            if l[1].filename.strip("/").count("/") > 0:
                self.name = l[0].filename.strip("/")
                logger.debug("Only one folder found in the zipfile: " + self.name)
                z.extractall(settings.PELICAN_THEMES)
            else:
                logger.debug("Archive contains multiple files - extracting to: " + self.path)
                z.extractall(self.path)
            z.close()
            zip_path.unlink()
        else:
            if self.url.startswith("https") and not self.url.endswith(".git"):
                self.url += ".git"
            proc = None
            if self.downloaded:
                proc = subprocess.Popen( # update
                    ["git", "pull"], cwd=str(self.path),
                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
            else:
                proc = subprocess.Popen( # download
                    ["git", "clone", "--recurse-submodules", self.url, self.name],
                    cwd=settings.PELICAN_THEMES, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
            if proc.wait() == 0:
                self.log = None
            else:
                self.log = proc.stdout.read()
                logger.error(self.log)
                if save:
                    self.save()
                return False

        image_paths = [path for path in Path(self.path).iterdir()
            if path.suffix in (".jpg", ".jpeg", ".png")]
        logger.debug(f"Found {len(image_paths)} images {image_paths}")
        self.image = File(image_paths[0].open("rb")) if len(image_paths) > 0 else None
        self.image1 = File(image_paths[1].open("rb")) if len(image_paths) > 1 else None
        self.image2 = File(image_paths[2].open("rb")) if len(image_paths) > 2 else None
        if not self.description:
            self.description = self.readme
        if save:
            self.save()
        return True

    @property
    def readme(self):
        for path in Path(self.path).iterdir():
            if "readme" in str(path).lower():
                return path.read_text(encoding="utf-8")
        return None

    def install(self, save=True):
        """Install the theme into pelican and django webserver"""
        if not self.downloaded:
            raise ValidationError("You must download the theme before installing it")
        if self.installed:
            return True
        try:
            pelican_themes.install(str(self.path), v=False)
        except Exception as e:
            self.log = str(e)
            logger.error(str(e))
        if save:
            self.save()

    def save(self, **kwargs):
        if not self.name:
            self.name = Path(self.url).stem
        if not self.downloaded:
            self.download(save=False)
        if self.downloaded and not self.installed:
            self.install(save=False)
        return super().save(**kwargs)

    def delete(self, **kwargs):
        pelican_themes.remove(self.name, v=False) # uninstall
        self.path.unlink() # remove
        return super().delete(**kwargs)

    def update(self, save=True):
        self.download(save=save)
        self.install(save=save)
        self.updated = datetime.now()
        if save:
            return self.save()

    def update_conf(self, conf):
        """Update site's pelican configuration using mapping that will requires specific keys"""
        if self.theme_settings:
            mapping = toml.loads(self.theme_settings)
            for key, value in mapping.items():
                if isinstance(value, str) and value.startswith("conf."):
                    conf_key = value.split(".")[1]
                    if conf_key in conf:
                        conf[key] = conf[conf_key]
                        logger.debug(f'Re-using conf.{conf_key} as key')
                    else:
                        logger.warn(f'Key "{conf_key}" does not exist in `conf`')
                else:
                    conf[key] = value
        return conf


class Settings(models.Model):
    POST_URL_TEMPLATES = (
        ('{slug}.html', f"<{_('slug')}>.html"),
        ('{slug}/index.html', f"<{_('slug')}>/index.html"),
        ('{date:%Y}/{slug}.html', f"<{_('year')}>/<{_('slug')}>.html"),
        ('{date:%Y}/{date:%b}/{slug}.html', f"<{_('year')}>/<{_('month')}>/<{_('slug')}>.html"),
        ('{category}/{slug}.html', f"<{_('author')}>/<{_('slug')}>.html"),
        ('{category}/{slug}.html', f"<{_('category')}>/<{_('slug')}>.html"),
        ('{category}/{date:%Y}/{slug}.html', f"<{_('category')}>/<{_('year')}>/<{_('slug')}>.html"),
    )
    site = models.OneToOneField(core.Site, related_name="pelican", on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.DO_NOTHING)
    show_pages_in_menu = models.BooleanField(default=True, null=False, help_text=_("Display pages in menu"))
    show_categories_in_menu = models.BooleanField(default=True, null=False, help_text=_("Display categories in menu"))
    post_url_template = models.CharField(max_length=255, choices=POST_URL_TEMPLATES, default=POST_URL_TEMPLATES[0][0])
    page_url_prefix = models.CharField(max_length=35, blank=True, default="", help_text=_("Pages URL prefix (pages urls will look like 'prefix/{slug}.html')"))
    category_url_prefix = models.CharField(max_length=35, default=_("category"), help_text=_("Category URL prefix (pages urls will look like 'prefix/{slug}.html')"))
    author_url_prefix = models.CharField(max_length=35, default=_("author"), help_text=_("Author URL prefix (pages urls will look like 'prefix/{slug}.html')"))
    tags_url_prefix = models.CharField(max_length=35, default=_("tags"), help_text=_("Tags URL prefix (it will look like 'prefix/{slug}.html')"))
    show_internal_pages_author = models.BooleanField(default=False, help_text=_("Include authors page"))
    show_internal_pages_categories = models.BooleanField(default=True, help_text=_("Include categories page"))
    show_internal_pages_tags = models.BooleanField(default=True, help_text=_("Include tags page"))
    facebook = models.CharField(max_length=128, null=True, blank=True)
    twitter = models.CharField(max_length=128, null=True, blank=True)
    linkedin = models.CharField(max_length=128, null=True, blank=True)
    github = models.CharField(max_length=128, null=True, blank=True)
    instagram = models.CharField(max_length=128, null=True, blank=True)
    plugins = models.ManyToManyField('pelican.Plugin', blank=True)

    class Meta:
        verbose_name = _("Settings")
        verbose_name_plural = _("Settings")

    __str__  = lambda self: str(self.site)

    @property
    def page_url_template(self):
        return ((self.page_url_prefix + "/") if self.page_url_prefix else "") + "{slug}.html"

    @property
    def category_url_template(self):
        return ((self.category_url_prefix + "/") if self.category_url_prefix else "") + "{slug}.html"

    @property
    def author_url_template(self):
        return ((self.author_url_prefix + "/") if self.author_url_prefix else "") + "index.html"

    @property
    def tags_url_template(self):
        return ((self.tags_url_prefix + "/") if self.tags_url_prefix else "") + "index.html"

    def save(self, **kwargs):
        conf = self.conf
        Path(conf["PATH"]).mkdir(exist_ok=True, parents=True)
        Path(conf["PATH"], conf['PAGE_PATHS'][0]).mkdir(exist_ok=True)
        Path(conf["PATH"], conf['ARTICLE_PATHS'][0]).mkdir(exist_ok=True)
        Path(conf["OUTPUT_PATH"]).mkdir(exist_ok=True, parents=True)
        return super().save(**kwargs)

    def delete(self, **kwargs):
        shutil.rmtree(self.get_source_path())
        shutil.rmtree(self.get_output_path())
        return super().delete(**kwargs)

    @property
    def conf(self):
        if hasattr(self, '_settings'):
            return self._settings
        self._settings = dict()
        self._settings.update(pelican.settings.DEFAULT_CONFIG)
        self._settings.update(settings.PELICAN_DEFAULT_SETTINGS)
        self._settings.update({
            'PATH': str(settings.PELICAN_CONTENT / self.site.domain / self.site.path),
            'ARTICLE_URL': (self.post_url_template if not self.post_url_template.endswith("index.html") else self.post_url_template[:-10]).lstrip("/"),
            'ARTICLE_SAVE_AS': self.post_url_template,
            'PAGE_URL': self.page_url_template,
            'PAGE_SAVE_AS': self.page_url_template,
            'TAGS_URL': self.tags_url_template,
            'TAGS_SAVE_AS': self.tags_url_template,
            'CATEGORY_URL': self.category_url_template,
            'CATEGORY_SAVE_AS': self.category_url_template,
            'AUTHOR_URL': self.author_url_template,
            'AUTHOR_SAVE_AS': self.author_url_template,
            'OUTPUT_PATH': str(settings.PELICAN_OUTPUT / self.site.domain / self.site.path),
            'THEME': str(Path(pelican_themes._THEMES_PATH, self.theme.name)),
            # Why the heck the dafault PAGINATION_PATTERNS are broken?!
            'PAGINATION_PATTERNS': [pelican.paginator.PaginationRule(*x) for x in pelican.settings.DEFAULT_CONFIG['PAGINATION_PATTERNS']],
            'FACEBOOK_PROFILE': self.facebook,
            'TWITTER_PROFILE': self.twitter,
            'LINKEDIN_PROFILE': self.linkedin,
            'GITHUB_PROFILE': self.github,
            'INSTAGRAM_PROFILE': self.instagram,
            'DISPLAY_CATEGORIES_ON_MENU': self.show_categories_in_menu,
            'DISPLAY_PAGES_ON_MENU': self.show_pages_in_menu,
            'ROBOTS': "noindex" if self.site.allow_crawlers else "all",
        })

        social = []
        if self.facebook:
            social.append(('facebook', self.facebook))
        if self.twitter:
            social.append(('twitter', self.twitter))
        if self.linkedin:
            social.append(('linkedin', self.linkedin))
        if self.github:
            social.append(('github', self.github))
        if self.instagram:
            social.append(('instagram', self.instagram))
        if social:
            logger.debug(f"Social for {self}: {social}")
            self._settings.update(SOCIAL=social)

        plugins = list(Plugin.objects.all().filter(default=True).values_list("id", flat=True))
        for plugin in self.plugins.all():
            if plugin.default:
                plugins.remove(plugin.name)
            else:
                plugins.append(plugin.name)
        logger.debug(f"Plugins for {self}: {plugins}")
        self._settings.update(PLUGINS=plugins)

        # internal_menu_items = []
        # if self.show_internal_pages_tags:
        #     internal_menu_items.append((self.tags_url_prefix.title, self._settings['TAGS_URL'], self._settings['TAGS_SAVE_AS']))
        # if self.show_internal_pages_author:
        #     internal_menu_items.append((self.author_url_prefix.title, self._settings['AUTHOR_URL'], self._settings['AUTHOR_SAVE_AS']))
        # if self.show_internal_pages_categories:
        #     internal_menu_items.append((self.category_url_prefix.title, self._settings['CATEGORY_URL'], self._settings['CATEGORY_SAVE_AS']))
        # 'MENU_INTERNAL_PAGES': internal_menu_items

        self._settings.update({
            'SITEURL': self.site.absolutize("/"), # give the full URL for the root of the blog
            'SITENAME': self.site.title,
            'SITEDESCRIPTION': self.site.subtitle,
            'SITELOGO': self.site.logo.url,
            'FEED_DOMAIN': self.site.absolutize("/"), # give the full URL for the root of the blog
            'MENUITEMS': core.Link.objects.filter(site=self.site).values_list("title", "url"),
        })

        if self.site.webmentions:
            self._settings.update(WEBMENTION_URL=settings.WEBMENTION_URL)
        elif self.site.webmentions_external:
            self._settings.update(WEBMENTION_URL=self.site.webmentions_external)

        if self.site.matomo:
            self._settings.update(MATOMO_URL=self.site.matomo_external, MATOMO_SITE_ID=self.site.matomo_external_id)

        self.theme.update_conf(self._settings)
        self.user.update_conf(self._settings)
        return self._settings

    @property
    def user(self):
        instance, _ = ThemeSettings.objects.get_or_create(
            pelican=self,
            theme=self.theme,
            defaults={"settings": self.theme.user_settings}
        )
        return instance

    def get_source_path(self):
        """Returns source path for the site assigned to this pelican settings.
        
        Don't worry - themes and plugins are stored elsewhere.
        """
        return self.conf['PATH']

    def get_output_path(self):
        """Returns the output path for the site assigned to this pelican settings"""
        return self.conf['OUTPUT_PATH']

    def get_page_source_path(self, page: core.Page):
        return self.conf['PATH'] / self.conf['PAGE_PATHS'][0] / (page.slug + ".md")

    def get_post_source_path(self, post: core.Post):
        return self.conf['PATH'] / self.conf['ARTICLE_PATHS'][0] / (post.slug + ".md")

    def get_page_output_path(self, page: core.Page):
        return self.conf['OUTPUT_PATH'] / self.get_page_url(page)

    def get_post_output_path(self, post: core.Post):
        return self.conf['OUTPUT_PATH'] / self.get_post_url(post)

    def get_page_url(self, page: core.Page):
        """Return URL of given page."""
        return self.post_url_template.format(slug=page.slug)

    def get_post_url(self, post: core.Post):
        """Return URL of given post (containing index.html in case of pretty-urls)."""
        return self.post_url_template.format(
                slug=post.slug,
                date=post.created,
                category=post.category.slug if post.category else "",
                author=post.author.username if post.author else "",
                lang=post.lang,
            )


class ThemeSettings(models.Model):
    """Settings for a theme per site - each site can modify their theme settings"""
    pelican = models.ForeignKey(Settings, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    settings = models.TextField(blank=True, null=True, help_text="Define extra variables for the theme (using KEY = 'value' or KEY = conf.EXISTING_KEY)")

    class Meta:
        verbose_name = _("Theme Settings")
        verbose_name_plural = _("Theme Settings")

    __str__ = lambda self: f"{self.pelican} : {self.theme}"

    def update_conf(self, conf):
        """Update site's pelican configuration using mapping that will requires specific keys"""
        if self.settings:
            mapping = toml.loads(self.settings)
            for key, value in mapping.items():
                logger.debug(f"UserSettings is adding {key}={value}")
                conf[key] = value
        return conf

    def validate_settings(self, settings):
        try:
            toml.loads(settings)
        except Exception as e:
            raise ValidationError(e)


class Plugin(models.Model):
    """Available plugins"""
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=32, blank=True)
    url = models.CharField(max_length=265, blank=True, null=True, help_text="Null for built-in plugins")
    default = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = _("Plugin")
        verbose_name_plural = _("Plugins")

    __str__  = lambda self: self.name if not self.default else f"{self.name} (default)"

    def save(self, **kwargs):
        if not self.name:
            if self.id.startswith("pelican.plugins."):
                self.name = self.id.split(".")[-1]
            else:
                self.name = self.id
        return super().save(**kwargs)