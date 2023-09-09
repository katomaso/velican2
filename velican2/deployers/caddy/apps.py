import requests
import urllib3.exceptions

from . import logger
from .. import IDeployer
from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models.signals import post_save
from requests.exceptions import ConnectionError

class CaddyConfig(AppConfig, IDeployer):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.deployers.caddy'

    def is_available(self):
        try:
            requests.get(settings.CADDY_URL + "/config/")
            return True
        except ConnectionError:
            logger.error("Caddy unavailable at " + settings.CADDY_URL)
            return False

    def ready(self) -> None:
        self.is_available()

    def deploy(self, site, post=None, page=None, **kwargs):
        # make sure there is a caddy server with velican server config
        if requests.get(settings.CADDY_URL + "/config/apps/http/servers/velican/").status_code != 200:
            requests.post(settings.CADDY_URL + "/config/",
                        json={"apps":{ "http": { "servers": { "velican": { "listen": [ ":80", ":443" ], "routes": []}}}}}
                        )
        # just make sure that caddy points to the renderer's output
        routes = requests.get(settings.CADDY_URL + "/config/apps/http/servers/velican/routes/").json()
        logger.debug(f"Caddy routes {routes}")
        if routes and any(map(lambda h: site.domain in h['match'][0]['host'], routes)):
            logger.debug(f"Site {site.domain} already in caddy handlers")
            return
        requests.post(
            settings.CADDY_URL + "/config/apps/http/servers/velican/routes/",
            json={
                "match": [{"host":[site.domain,]}],
                "handle": [{
                    "handler": "file_server",
                    "root": str(site.get_engine().get_output_path(site))
                }]
            })

    def delete(self, site, post=None, page=None, **kwargs):
        # just make sure that caddy points to the renderer's output
        logger.info("Caddy delete is a noop")

