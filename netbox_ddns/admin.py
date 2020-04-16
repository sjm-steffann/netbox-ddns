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
from .background_tasks import update_dns
from .models import ReverseZone, Server, Zone

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
    list_display = ('server', 'tsig_key_name', 'tsig_algorithm')
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
            addresses = IPAddress.objects.filter(Q(dns_name__endswith=zone.name) |
                                                 Q(dns_name__endswith=zone.name.rstrip('.')))
            for more_specific in more_specifics:
                addresses = addresses.exclude(Q(dns_name__endswith=more_specific.name) |
                                              Q(dns_name__endswith=more_specific.name.rstrip('.')))

            for address in addresses:
                if address.dns_name:
                    update_dns.delay(
                        new_record=address,
                        skip_reverse=True
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
            addresses = IPAddress.objects.filter(address__net_contained=zone.prefix)
            for more_specific in more_specifics:
                addresses = addresses.exclude(address__net_contained=more_specific.prefix)

            for address in addresses:
                if address.dns_name:
                    update_dns.delay(
                        new_record=address,
                        skip_forward=True
                    )
                    counter += 1

            messages.info(request, _("Updating {count} reverse records in {name}").format(count=counter,
                                                                                          name=zone.name))
