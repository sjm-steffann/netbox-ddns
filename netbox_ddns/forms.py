from django import forms

from netbox_ddns.models import ExtraDNSName


class ExtraDNSNameEditForm(forms.ModelForm):
    class Meta:
        model = ExtraDNSName
        fields = ['name']
