import django.apps

deployers = ("caddy", "aws")

class IDeployer:
    """Interface of a deployer"""
    def deploy(self, site, post=None, page=None, **kwargs):
        raise NotImplementedError()

    def delete(self, site, post=None, page=None):
        raise NotImplementedError()


def get_deployer(deployer: str):
    if deployer not in deployers:
        raise RuntimeError(f"Deployer {deployer} does not exist")
    return django.apps.registry.apps.get_app_config(deployer)
