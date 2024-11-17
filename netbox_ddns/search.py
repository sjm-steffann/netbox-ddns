from netbox.search import SearchIndex, register_search
from .models import ExtraDNSName


@register_search
class AccessListIndex(SearchIndex):
    model = ExtraDNSName
    fields = (
        ('name', 100),
    )
