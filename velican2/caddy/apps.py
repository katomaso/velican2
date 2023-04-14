import requests
from velican2.caddy import logger
from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models.signals import post_save


def on_site_save(instance, **kwargs):
    """Register a new handler for the site/domain"""
    if instance.deployment != "caddy":
        logger.debug(f"Site {instance.domain} is not handled by caddy")
        return

    routes = requests.get(settings.CADDY_URL + "/config/apps/http/servers/velican/handlers/").json()
    if routes and instance.domain in list(map(lambda h: h['match'][0]['host'], routes)):
        logger.debug(f"Site {instance.domain} already in caddy handlers")
        return
    requests.post(
        settings.CADDY_URL + "/config/apps/http/servers/velican/routes/",
        json={
            "match": [{"host":[instance.domain,]}],
            "handle": [{
                "handler": "file_server",
                "root": str(instance.get_engine().get_publish_path())
            }]
        })


class CaddyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.caddy'

    def ready(self):
        if not settings.CADDY_URL:
            logger.warn(f"Caddy deployment disabled because of missing CADDY_URL settings")
            return

        try:
            # check whether caddy is running (throws an exception if point is unreachable)
            requests.get(settings.CADDY_URL, timeout=1)

            post_save.connect(on_site_save, sender=apps.get_model("core", "Site"))

            # make sure there is a caddy server with velican server config
            if requests.get(settings.CADDY_URL + "/config/apps/http/servers/velican/").status_code != 200:
                requests.post(settings.CADDY_URL + "/config/",
                            json={"apps":{ "http": { "servers": { "velican": { "listen": [ ":80", ":443" ], "routes": []}}}}}
                            )
        except requests.ConnectTimeout as cto:
            logger.error("Caddy initial connection timed out. Not allowing caddy deploy")