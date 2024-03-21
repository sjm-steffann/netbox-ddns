import django_tables2 as tables

from netbox_ddns.models import ExtraDNSName
try:
    # NetBox >= 3.2.0
    from netbox.tables import BaseTable
    from netbox.tables.columns import ToggleColumn, DateTimeColumn
except ImportError:
    # NetBox < 3.2.0
    from utilities.tables import BaseTable, ToggleColumn, DateTimeColumn

FORWARD_DNS = """
    {% if record.forward_action is not None %}
        {{ record.get_forward_action_display }}:
        {{ record.get_forward_rcode_html_display }}
    {% else %}
        <span class="text-muted">Not created</span>
    {% endif %}
"""

ACTIONS = """
    {% if perms.netbox_ddns.change_extradnsname %}
        <a href="{% url 'plugins:netbox_ddns:extradnsname_edit' ipaddress_pk=record.ip_address.pk pk=record.pk %}" 
           class="btn btn-sm btn-warning">
            <i class="mdi mdi-pencil" aria-hidden="true"></i>
        </a>
    {% endif %}
    {% if perms.netbox_ddns.delete_extradnsname %}
        <a href="{% url 'plugins:netbox_ddns:extradnsname_delete' ipaddress_pk=record.ip_address.pk pk=record.pk %}"
           class="btn btn-sm btn-danger">
            <i class="mdi mdi-trash-can-outline" aria-hidden="true"></i>
        </a>
    {% endif %}
"""


class PrefixTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column()
    last_update = DateTimeColumn()
    forward_dns = tables.TemplateColumn(template_code=FORWARD_DNS)
    actions = tables.TemplateColumn(
        template_code=ACTIONS,
        attrs={'td': {'class': 'text-right text-nowrap noprint'}},
        verbose_name=''
    )

    class Meta(BaseTable.Meta):
        model = ExtraDNSName
        fields = ('pk', 'name', 'last_update', 'forward_dns', 'actions')
