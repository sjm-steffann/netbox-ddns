import logging

from django.contrib import admin, messages
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.options import ModelAdmin
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from ipam.models import IPAddress
from netbox.admin import admin_site
from netbox_ddns.models import DNSStatus, ExtraDNSName
from .background_tasks import dns_create
from .models import ReverseZone, Server, Zone
from .utils import normalize_fqdn

logger = logging.getLogger('netbox_ddns')


class IPFamilyFilter(SimpleListFilter):
    title = _('Prefix family')
    parameter_name = 'family'

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin):
        return (
            ('ipv4', _('IPv4')),
            ('ipv6', _('IPv6')),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if self.value() == 'ipv4':
            return queryset.filter(prefix__family=4)
        if self.value() == 'ipv6':
            return queryset.filter(prefix__family=6)


class ZoneInlineAdmin(admin.TabularInline):
    model = Zone


class ReverseZoneInlineAdmin(admin.TabularInline):
    model = ReverseZone


@admin.register(Server, site=admin_site)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('server', 'server_port', 'tsig_key_name', 'tsig_algorithm')
    inlines = [
        ZoneInlineAdmin,
        ReverseZoneInlineAdmin,
    ]


@admin.register(Zone, site=admin_site)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'ttl', 'server')
    actions = [
        'update_all_records'
    ]

    def update_all_records(self, request: HttpRequest, queryset: QuerySet):
        for zone in queryset:
            counter = 0

            # Find all more-specific zones
            more_specifics = Zone.objects.filter(name__endswith=zone.name).exclude(pk=zone.pk)

            # Find all IPAddress objects in this zone but not in the more-specifics
            ip_addresses = IPAddress.objects.filter(Q(dns_name__endswith=zone.name) |
                                                    Q(dns_name__endswith=zone.name.rstrip('.')))
            for more_specific in more_specifics:
                ip_addresses = ip_addresses.exclude(Q(dns_name__endswith=more_specific.name) |
                                                    Q(dns_name__endswith=more_specific.name.rstrip('.')))

            for ip_address in ip_addresses:
                new_address = ip_address.address.ip
                new_dns_name = normalize_fqdn(ip_address.dns_name)

                if new_dns_name:
                    status, created = DNSStatus.objects.get_or_create(ip_address=ip_address)

                    dns_create.delay(
                        dns_name=new_dns_name,
                        address=new_address,
                        status=status,
                        reverse=False,
                    )

                    counter += 1

            # Find all ExtraDNSName objects in this zone but not in the more-specifics
            extra_names = ExtraDNSName.objects.filter(name__endswith=zone.name)
            for more_specific in more_specifics:
                extra_names = extra_names.exclude(name__endswith=more_specific.name)

            for extra in extra_names:
                new_address = extra.ip_address.address.ip
                new_dns_name = extra.name

                dns_create.delay(
                    dns_name=new_dns_name,
                    address=new_address,
                    status=extra,
                    reverse=False,
                )

                counter += 1

            messages.info(request, _("Updating {count} forward records in {name}").format(count=counter,
                                                                                          name=zone.name))


@admin.register(ReverseZone, site=admin_site)
class ReverseZoneAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'name', 'ttl', 'server')
    list_filter = [IPFamilyFilter]
    actions = [
        'update_all_records'
    ]

    def update_all_records(self, request: HttpRequest, queryset: QuerySet):
        for zone in queryset:
            counter = 0

            # Find all more-specific zones
            more_specifics = ReverseZone.objects.filter(prefix__net_contained=zone.prefix).exclude(pk=zone.pk)

            # Find all IPAddress objects in this zone but not in the more-specifics
            ip_addresses = IPAddress.objects.filter(address__net_contained_or_equal=zone.prefix)
            for more_specific in more_specifics:
                ip_addresses = ip_addresses.exclude(address__net_contained_or_equal=more_specific.prefix)

            for ip_address in ip_addresses:
                new_address = ip_address.address.ip
                new_dns_name = normalize_fqdn(ip_address.dns_name)

                if new_dns_name:
                    status, created = DNSStatus.objects.get_or_create(ip_address=ip_address)

                    dns_create.delay(
                        dns_name=new_dns_name,
                        address=new_address,
                        status=status,
                        forward=False,
                    )

                    counter += 1

            messages.info(request, _("Updating {count} reverse records in {name}").format(count=counter,
                                                                                          name=zone.name))


@admin.register(ExtraDNSName, site=admin_site)
class ExtraDNSNameAdmin(admin.ModelAdmin):
    pass
