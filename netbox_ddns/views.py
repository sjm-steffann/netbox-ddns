from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import is_safe_url

from ipam.models import IPAddress
from netbox_ddns.forms import ExtraDNSNameEditForm
from netbox_ddns.models import ExtraDNSName
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
