from django.urls import path

from .views import ExtraDNSNameCreateView, ExtraDNSNameDeleteView, ExtraDNSNameEditView, IPAddressDNSNameRecreateView

urlpatterns = [
    path(route='ip-addresses/<int:ipaddress_pk>/recreate/',
         view=IPAddressDNSNameRecreateView.as_view(),
         name='ipaddress_dnsname_recreate'),
    path(route='ip-addresses/<int:ipaddress_pk>/extra/create/',
         view=ExtraDNSNameCreateView.as_view(),
         name='extradnsname_create'),
    path(route='ip-addresses/<int:ipaddress_pk>/extra/<int:pk>/edit/',
         view=ExtraDNSNameEditView.as_view(),
         name='extradnsname_edit'),
    path(route='ip-addresses/<int:ipaddress_pk>/extra/<int:pk>/delete/',
         view=ExtraDNSNameDeleteView.as_view(),
         name='extradnsname_delete'),
]
