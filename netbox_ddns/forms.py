from django import forms

from netbox_ddns.models import ExtraDNSName
from utilities.forms import BootstrapMixin


class ExtraDNSNameEditForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ExtraDNSName
        fields = ['name']
