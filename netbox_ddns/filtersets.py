from netbox.filtersets import NetBoxModelFilterSet
from .models import ExtraDNSName


class ExtraDNSNameFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = ExtraDNSName
        fields = ('id', 'name', 'ip_address', 'forward_rcode')
