# Dynamic DNS Connector for NetBox

This plugin lets you define DNS servers that support [RFC3007 Dynamic DNS Updates](https://tools.ietf.org/html/rfc3007). For each server you specify which domains and reverse DNS domains it is responsible for, and after that NetBox will automatically send DNS Updates to those servers whenever you change the DNS name of an IP Address in NetBox.

Updates are sent from the worker process in the background. You can see their progress either by configuring Django logging or by looking at the Background Tasks in the NetBox admin back-end.

For now all configuration is done in the NetBox admin back-end. A later version will provide a nicer user interface.

## Compatibility

This plugin in compatible with [NetBox](https://netbox.readthedocs.org/) 2.8 and later.
