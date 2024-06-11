# Dynamic DNS Connector for NetBox

This plugin lets you define DNS servers that support [RFC3007 Dynamic DNS Updates](https://tools.ietf.org/html/rfc3007).
For each server you specify which domains and reverse DNS domains it is responsible for, and after that NetBox will
automatically send DNS Updates to those servers whenever you change the DNS name of an IP Address in NetBox.

Updates are sent from the worker process in the background. You can see their progress either by configuring Django
logging or by looking at the Background Tasks in the NetBox admin back-end.

For now all configuration is done in the NetBox admin back-end. A later version will provide a nicer user interface.

## Compatibility

This plugin in compatible with [NetBox](https://netbox.readthedocs.org/) v3.0.0 and greater, support for Netbox v2.11.0 is dropped in v1.1.4 due to UI implementation.

> [!Important]
> Netbox 4.0 - Admin interface disabled by default<br />
> Can be re-enabled by specifying `DJANGO_ADMIN_ENABLED = True` in `configuration.py`<br />
> If static files are not loaded, re-run `upgrade.sh` this will copy back the required static assets.


## Installation

First, add `netbox-ddns` to your `/opt/netbox/local_requirements.txt` file. Create it if it doesn't exist.

Then enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`, like:

```python
PLUGINS = [
    'netbox_ddns',
]
```

And finally run `/opt/netbox/upgrade.sh`. This will download and install the plugin and update the database when
necessary. Don't forget to run `sudo systemctl restart netbox netbox-rq` like `upgrade.sh` tells you!
