from django.contrib.auth.context_processors import PermWrapper

from extras.plugins import PluginTemplateExtension


# noinspection PyAbstractClass
class DNSInfo(PluginTemplateExtension):
    model = 'ipam.ipaddress'

    def left_page(self):
        """
        An info-box with edit button for the vCenter settings
        """
        return self.render('netbox_ddns/ipaddress/dns_info.html')


template_extensions = [DNSInfo]
