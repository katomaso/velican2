import requests

# from sqlalchemy import event
from models import Site
from velican.app import app, db

def register_domain_to_caddy(instance: Site):
    """Let caddy know about new routing"""
    requests.post("caddy-admin:9900", {"route": ...})

def init():
    pass
    #event.listen(Site, "before_insert", register_domain_to_caddy, propagate=True)

def config():
    return None