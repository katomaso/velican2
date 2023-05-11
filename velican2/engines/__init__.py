import django.apps

engines = ("pelican", )

def get_engine(engine: str):
    if engine not in engines:
        raise RuntimeError(f"Engine {engine} does not exist")
    return django.apps.registry.apps.get_app_config(engine)
