from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from ipam.models import IPAddress
from netbox.api.serializers import NetBoxModelSerializer
from ..models import ExtraDNSName


class ExtraDNSNameSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_ddns-api:extradnsname-detail'
    )
    ip_address = PrimaryKeyRelatedField(queryset=IPAddress.objects.all(),)

    class Meta:
        model = ExtraDNSName
        fields = ('id', 'ip_address', 'name', 'url')
        read_only_fields = ('id', 'url')
