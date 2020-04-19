from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from django.views import View

from ipam.models import IPAddress
from netbox_ddns.background_tasks import dns_create
from netbox_ddns.forms import ExtraDNSNameEditForm
from netbox_ddns.models import DNSStatus, ExtraDNSName, Zone
from netbox_ddns.utils import normalize_fqdn
from utilities.views import ObjectDeleteView, ObjectEditView


class ExtraDNSNameObjectMixin:
    def get_object(self, kwargs):
        if 'ipaddress_pk' not in kwargs:
            raise Http404

        ip_address = get_object_or_404(IPAddress, pk=kwargs['ipaddress_pk'])

        if 'pk' in kwargs:
            return get_object_or_404(ExtraDNSName, ip_address=ip_address, pk=kwargs['pk'])

        return ExtraDNSName(ip_address=ip_address)

    def get_return_url(self, request, obj=None):
        # First, see if `return_url` was specified as a query parameter or form data. Use this URL only if it's
        # considered safe.
        query_param = request.GET.get('return_url') or request.POST.get('return_url')
        if query_param and is_safe_url(url=query_param, allowed_hosts=request.get_host()):
            return query_param

        # Otherwise check we have an object and can return to its ip-address
        elif obj is not None and obj.ip_address is not None:
            return obj.ip_address.get_absolute_url()

        # If all else fails, return home. Ideally this should never happen.
        return reverse('home')


class ExtraDNSNameCreateView(PermissionRequiredMixin, ExtraDNSNameObjectMixin, ObjectEditView):
    permission_required = 'netbox_ddns.add_extradnsname'
    model = ExtraDNSName
    model_form = ExtraDNSNameEditForm


class ExtraDNSNameEditView(ExtraDNSNameCreateView):
    permission_required = 'netbox_ddns.change_extradnsname'


class ExtraDNSNameDeleteView(PermissionRequiredMixin, ExtraDNSNameObjectMixin, ObjectDeleteView):
    permission_required = 'netbox_ddns.delete_extradnsname'
    model = ExtraDNSName


class IPAddressDNSNameRecreateView(PermissionRequiredMixin, View):
    permission_required = 'ipam.change_ipaddress'

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
