import django_tables2 as tables

from netbox_ddns.models import ExtraDNSName
from utilities.tables import BaseTable, ToggleColumn

FORWARD_DNS = """
    {% if record.forward_action is not None %}
        {{ record.get_forward_action_display }}:
        {{ record.get_forward_rcode_html_display }}
    {% else %}
        <span class="text-muted">Not created</span>
    {% endif %}
"""

ACTIONS = """
    {% if perms.dcim.change_extradnsname %}
        <a href="{% url 'plugins:netbox_ddns:extradnsname_edit' ipaddress_pk=record.ip_address.pk pk=record.pk %}" 
           class="btn btn-xs btn-warning">
            <i class="glyphicon glyphicon-pencil" aria-hidden="true"></i>
        </a>
    {% endif %}
    {% if perms.dcim.delete_extradnsname %}
        <a href="{% url 'plugins:netbox_ddns:extradnsname_delete' ipaddress_pk=record.ip_address.pk pk=record.pk %}"
           class="btn btn-xs btn-danger">
            <i class="glyphicon glyphicon-trash" aria-hidden="true"></i>
        </a>
    {% endif %}
"""


class PrefixTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column()
    last_update = tables.Column()
    forward_dns = tables.TemplateColumn(template_code=FORWARD_DNS)
    actions = tables.TemplateColumn(
        template_code=ACTIONS,
        attrs={'td': {'class': 'text-right text-nowrap noprint'}},
        verbose_name=''
    )

    class Meta(BaseTable.Meta):
        model = ExtraDNSName
        fields = ('pk', 'name', 'last_update', 'forward_dns', 'actions')
