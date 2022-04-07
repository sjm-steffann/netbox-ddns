from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from ipam.models import IPAddress
from netbox_ddns.background_tasks import dns_create
from netbox_ddns.forms import ExtraDNSNameEditForm
from netbox_ddns.models import DNSStatus, ExtraDNSName
from netbox_ddns.utils import normalize_fqdn

try:
    # NetBox <= 2.9
    from utilities.views import ObjectDeleteView, ObjectEditView
except ImportError:
    # NetBox >= 2.10
    from netbox.views.generic import ObjectDeleteView, ObjectEditView


# noinspection PyMethodMayBeStatic
class ExtraDNSNameObjectMixin:
    def get_object(self, *args, **kwargs):
        # NetBox < 3.2.0
        if not kwargs and len(args) == 1:
            kwargs = args[0]
        elif len(args) > 1:
            raise TypeError('Method takes 1 positional argument but more were given')

        if 'ipaddress_pk' not in kwargs:
            raise Http404

        ip_address = get_object_or_404(IPAddress, pk=kwargs['ipaddress_pk'])

        if 'pk' in kwargs:
            return get_object_or_404(ExtraDNSName, ip_address=ip_address, pk=kwargs['pk'])

        return ExtraDNSName(ip_address=ip_address)

    def get_return_url(self, request, obj=None):
        # First, see if `return_url` was specified as a query parameter or form data. Use this URL only if it's
        # considered safe.
        return_url = request.GET.get('return_url') or request.POST.get('return_url')
        if return_url and return_url.startswith('/'):
            return return_url

        # Otherwise check we have an object and can return to its ip-address
        elif obj is not None and obj.ip_address is not None:
            return obj.ip_address.get_absolute_url()

        # If all else fails, return home. Ideally this should never happen.
        return reverse('home')


class ExtraDNSNameCreateView(PermissionRequiredMixin, ExtraDNSNameObjectMixin, ObjectEditView):
    permission_required = 'netbox_ddns.add_extradnsname'
    queryset = ExtraDNSName.objects.all()
    form = ExtraDNSNameEditForm
    # NetBox < 3.2.0
    @property
    def model_form(self):
        return self.form

class ExtraDNSNameEditView(ExtraDNSNameCreateView):
    permission_required = 'netbox_ddns.change_extradnsname'


class ExtraDNSNameDeleteView(PermissionRequiredMixin, ExtraDNSNameObjectMixin, ObjectDeleteView):
    permission_required = 'netbox_ddns.delete_extradnsname'
    queryset = ExtraDNSName.objects.all()


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
