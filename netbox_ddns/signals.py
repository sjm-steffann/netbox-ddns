import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from ipam.models import IPAddress
from netbox_ddns.background_tasks import update_dns

logger = logging.getLogger('netbox_ddns')


@receiver(pre_save, sender=IPAddress)
def store_original_ipaddress(instance: IPAddress, **_kwargs):
    instance.before_save = IPAddress.objects.filter(pk=instance.pk).first()


@receiver(post_save, sender=IPAddress)
def trigger_ddns_update(instance: IPAddress, **_kwargs):
    old_address = instance.before_save.address if instance.before_save else None
    old_dns_name = instance.before_save.dns_name if instance.before_save else ''

    if instance.address != old_address or instance.dns_name != old_dns_name:
        # IP address or DNS name has changed
        update_dns.delay(
            old_record=instance.before_save,
            new_record=instance,
        )


@receiver(post_delete, sender=IPAddress)
def trigger_ddns_delete(instance: IPAddress, **_kwargs):
    update_dns.delay(
        old_record=instance,
    )
