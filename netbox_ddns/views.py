from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from ipam.models import IPAddress
from netbox_ddns.background_tasks import dns_create
from netbox_ddns.forms import ExtraDNSNameEditForm
from netbox_ddns.models import DNSStatus, ExtraDNSName
from netbox_ddns.utils import normalize_fqdn

from utilities.forms import ConfirmationForm
from utilities.htmx import htmx_partial
from utilities.views import get_viewname

from netbox.views.generic import ObjectDeleteView, ObjectEditView, ObjectView


class ExtraDNSNameCreateView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'netbox_ddns.add_extradnsname'
    queryset = ExtraDNSName.objects.all()
    form = ExtraDNSNameEditForm

    def get_object(self, *args, **kwargs):
        ip_address = get_object_or_404(IPAddress, pk=kwargs['ipaddress_pk'])
        return ExtraDNSName(ip_address=ip_address)


class ExtraDNSNameView(PermissionRequiredMixin, ObjectView):
    permission_required = 'netbox_ddns.view_extradnsname'
    queryset = ExtraDNSName.objects.all()


class ExtraDNSNameEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'netbox_ddns.change_extradnsname'
    queryset = ExtraDNSName.objects.all()
    form = ExtraDNSNameEditForm

    def get_object(self, *args, **kwargs):
        return get_object_or_404(ExtraDNSName, pk=kwargs['pk'])


class ExtraDNSNameDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'netbox_ddns.delete_extradnsname'
    queryset = ExtraDNSName.objects.all()

    def get_return_url(self, request, obj=None):
        if obj and obj.ip_address:
            return obj.ip_address.get_absolute_url()
        return super().get_return_url(request, obj)


class IPAddressDNSNameRecreateView(PermissionRequiredMixin, View):
    permission_required = 'ipam.change_ipaddress'

    # noinspection PyMethodMayBeStatic
    def post(self, request, ipaddress_pk):
        ip_address = get_object_or_404(IPAddress, pk=ipaddress_pk)

        new_address = ip_address.address.ip
        new_dns_name = normalize_fqdn(ip_address.dns_name)

        updated_names = []

        if new_dns_name:
            status, created = DNSStatus.objects.get_or_create(ip_address=ip_address)

            dns_create.delay(
                dns_name=new_dns_name,
                address=new_address,
                status=status,
            )

            updated_names.append(new_dns_name)

        for extra in ip_address.extradnsname_set.all():
            new_address = extra.ip_address.address.ip
            new_dns_name = extra.name

            dns_create.delay(
                dns_name=new_dns_name,
                address=new_address,
                status=extra,
                reverse=False,
            )

            updated_names.append(new_dns_name)

        if updated_names:
            messages.info(request, _("Updating DNS for {names}").format(names=', '.join(updated_names)))

        return redirect('ipam:ipaddress', pk=ip_address.pk)
