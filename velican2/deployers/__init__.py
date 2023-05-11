import django.apps

deployers = ("caddy", "aws")

def get_deployer(deployer: str):
    if deployer not in deployers:
        raise RuntimeError(f"Deployer {deployer} does not exist")
    return django.apps.registry.apps.get_app_config(deployer)
