import django.apps

exporters = ("git", )

class IExporter:
    def is_available(self):
        raise NotImplementedError()

    def is_active(self, site):
        raise NotImplementedError()


def get_exporter(exporter: str):
    if exporter not in exporters:
        raise RuntimeError(f"exporter {exporter} does not exist")
    return django.apps.registry.apps.get_app_config(exporter)
