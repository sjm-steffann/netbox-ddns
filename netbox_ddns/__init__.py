VERSION = '1.1.0'

try:
    from extras.plugins import PluginConfig
except ImportError:
    # Dummy for when importing outside of netbox
    class PluginConfig:
        pass


class NetBoxDDNSConfig(PluginConfig):
    name = 'netbox_ddns'
    verbose_name = 'Dynamic DNS'
    version = VERSION
    min_version = '2.8'
    max_version = '2.10'
    author = 'Sander Steffann'
    author_email = 'sander@steffann.nl'
    description = 'Dynamic DNS Connector for NetBox'
    base_url = 'ddns'
    required_settings = []
    default_settings = {}

    def ready(self):
        super().ready()

        from . import signals


config = NetBoxDDNSConfig
