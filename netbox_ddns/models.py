import logging
import socket
from typing import Optional

import dns.tsigkeyring
import dns.update
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from dns import rcode
from dns.tsig import HMAC_MD5, HMAC_SHA1, HMAC_SHA224, HMAC_SHA256, HMAC_SHA384, HMAC_SHA512
from netaddr import ip

from ipam.fields import IPNetworkField
from ipam.models import IPAddress
from .validators import HostnameAddressValidator, HostnameValidator, validate_base64

logger = logging.getLogger('netbox_ddns')

TSIG_ALGORITHM_CHOICES = (
    (str(HMAC_MD5), 'HMAC MD5'),
    (str(HMAC_SHA1), 'HMAC SHA1'),
    (str(HMAC_SHA224), 'HMAC SHA224'),
    (str(HMAC_SHA256), 'HMAC SHA256'),
    (str(HMAC_SHA384), 'HMAC SHA384'),
    (str(HMAC_SHA512), 'HMAC SHA512'),
)

ACTION_CREATE = 1
ACTION_DELETE = 2

ACTION_CHOICES = (
    (ACTION_CREATE, 'Create'),
    (ACTION_DELETE, 'Delete'),
)


def get_rcode_display(code):
    if code is None:
        return None
    elif code == rcode.NOERROR:
        return _('Success')
    elif code == rcode.SERVFAIL:
        return _('Server failure')
    elif code == rcode.NXDOMAIN:
        return _('Name does not exist')
    elif code == rcode.NOTIMP:
        return _('Not implemented')
    elif code == rcode.REFUSED:
        return _('Refused')
    elif code == rcode.NOTAUTH:
        return _('Server not authoritative')
    else:
        return _('Unknown response: {}').format(code)


class Server(models.Model):
    server = models.CharField(
        verbose_name=_('DDNS Server'),
        max_length=255,
        validators=[HostnameAddressValidator()],
    )
    tsig_key_name = models.CharField(
        verbose_name=_('TSIG Key Name'),
        max_length=255,
        validators=[HostnameValidator()],
    )
    tsig_algorithm = models.CharField(
        verbose_name=_('TSIG Algorithm'),
        max_length=32,  # Longest is 24 chars for historic reasons, new ones are shorter, so 32 is more than enough
        choices=TSIG_ALGORITHM_CHOICES,
    )
    tsig_key = models.CharField(
        verbose_name=_('TSIG Key'),
        max_length=512,
        validators=[validate_base64],
        help_text=_('in base64 notation'),
    )

    class Meta:
        unique_together = (
            ('server', 'tsig_key_name'),
        )
        ordering = ('server', 'tsig_key_name')
        verbose_name = _('dynamic DNS Server')
        verbose_name_plural = _('dynamic DNS Servers')

    def __str__(self):
        return f'{self.server} ({self.tsig_key_name})'

    def clean(self):
        # Remove trailing dots from the server name/address
        self.server = self.server.lower().rstrip('.')

        # Ensure trailing dots from domain-style fields
        self.tsig_key_name = self.tsig_key_name.lower().rstrip('.') + '.'

    @property
    def address(self) -> Optional[str]:
        addrinfo = socket.getaddrinfo(self.server, 'domain', proto=socket.IPPROTO_UDP)
        for family, _, _, _, sockaddr in addrinfo:
            if family in (socket.AF_INET, socket.AF_INET6) and sockaddr[0]:
                return sockaddr[0]

    def create_update(self, zone: str) -> dns.update.Update:
        return dns.update.Update(
            zone=zone.rstrip('.') + '.',
            keyring=dns.tsigkeyring.from_text({
                self.tsig_key_name: self.tsig_key
            }),
            keyname=self.tsig_key_name,
            keyalgorithm=self.tsig_algorithm
        )


class Zone(models.Model):
    name = models.CharField(
        verbose_name=_('zone name'),
        max_length=255,
        validators=[HostnameValidator()],
        unique=True,
    )
    ttl = models.PositiveIntegerField(
        verbose_name=_('TTL'),
    )
    server = models.ForeignKey(
        to=Server,
        verbose_name=_('DDNS Server'),
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = _('zone')
        verbose_name_plural = _('zones')

    def __str__(self):
        return self.name

    def clean(self):
        # Ensure trailing dots from domain-style fields
        self.name = self.name.lower().rstrip('.') + '.'

    def get_updater(self):
        return self.server.create_update(self.name)


class ReverseZone(models.Model):
    prefix = IPNetworkField(
        verbose_name=_('prefix'),
        unique=True,
    )
    name = models.CharField(
        verbose_name=_('reverse zone name'),
        max_length=255,
        blank=True,
        help_text=_("RFC 2317 style reverse DNS, required when the prefix doesn't map to a reverse zone"),
    )
    ttl = models.PositiveIntegerField(
        verbose_name=_('TTL'),
    )
    server = models.ForeignKey(
        to=Server,
        verbose_name=_('DDNS Server'),
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ('prefix',)
        verbose_name = _('reverse zone')
        verbose_name_plural = _('reverse zones')

    def __str__(self):
        return f'for {self.prefix}'

    def record_name(self, address: ip.IPAddress):
        record_name = self.name
        if self.prefix.version == 4:
            for pos, octet in enumerate(address.words):
                if (pos + 1) * 8 <= self.prefix.prefixlen:
                    continue

                record_name = f'{octet}.{record_name}'
        else:
            nibbles = f'{address.value:032x}'
            for pos, nibble in enumerate(nibbles):
                if (pos + 1) * 4 <= self.prefix.prefixlen:
                    continue

                record_name = f'{nibble}.{record_name}'

        return record_name

    def clean(self):
        if self.prefix.version == 4:
            if self.prefix.prefixlen not in [0, 8, 16, 24] and not self.name:
                raise ValidationError({
                    'name': _('Required when prefix length is not 0, 8, 16 or 24'),
                })
            elif not self.name:
                # Generate it for the user
                self.name = 'in-addr.arpa'
                for pos, octet in enumerate(self.prefix.ip.words):
                    if pos * 8 >= self.prefix.prefixlen:
                        break

                    self.name = f'{octet}.{self.name}'
        else:
            if self.prefix.prefixlen % 4 != 0 and not self.name:
                raise ValidationError({
                    'name': _('Required when prefix length is not a nibble boundary'),
                })
            elif not self.name:
                # Generate it for the user
                self.name = 'ip6.arpa'
                nibbles = f'{self.prefix.ip.value:032x}'
                for pos, nibble in enumerate(nibbles):
                    if pos * 4 >= self.prefix.prefixlen:
                        break

                    self.name = f'{nibble}.{self.name}'

        # Ensure trailing dots from domain-style fields
        self.name = self.name.lower().rstrip('.') + '.'


class DNSStatus(models.Model):
    ip_address = models.OneToOneField(
        to=IPAddress,
        verbose_name=_('IP address'),
        on_delete=models.CASCADE,
    )
    last_update = models.DateTimeField(
        verbose_name=_('last update'),
        auto_now=True,
    )

    forward_action = models.PositiveSmallIntegerField(
        verbose_name=_('forward record action'),
        choices=ACTION_CHOICES,
        blank=True,
        null=True,
    )
    forward_rcode = models.PositiveIntegerField(
        verbose_name=_('forward record response'),
        blank=True,
        null=True,
    )

    reverse_action = models.PositiveSmallIntegerField(
        verbose_name=_('reverse record action'),
        choices=ACTION_CHOICES,
        blank=True,
        null=True,
    )
    reverse_rcode = models.PositiveIntegerField(
        verbose_name=_('reverse record response'),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('DNS status')
        verbose_name_plural = _('DNS status')

    def get_forward_rcode_display(self) -> Optional[str]:
        return get_rcode_display(self.forward_rcode)

    def get_reverse_rcode_display(self) -> Optional[str]:
        return get_rcode_display(self.reverse_rcode)
