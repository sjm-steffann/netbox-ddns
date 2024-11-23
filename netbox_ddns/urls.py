from django.urls import path

from .views import ExtraDNSNameCreateView, ExtraDNSNameDeleteView, ExtraDNSNameEditView, IPAddressDNSNameRecreateView, ExtraDNSNameView

urlpatterns = [
    path(route='ip-addresses/<int:ipaddress_pk>/recreate/',
         view=IPAddressDNSNameRecreateView.as_view(),
         name='ipaddress_dnsname_recreate'),
    path(route='ip-addresses/<int:ipaddress_pk>/extra-dns-name/create/',
         view=ExtraDNSNameCreateView.as_view(),
         name='extradnsname_create'),
    path(route='extra-dns-name/<int:pk>/edit/',
         view=ExtraDNSNameEditView.as_view(),
         name='extradnsname_edit'),
    path(route='extra-dns-name/<int:pk>/delete/',
         view=ExtraDNSNameDeleteView.as_view(),
         name='extradnsname_delete'),
    path(route='extra-dns-name/<int:pk>/',
         view=ExtraDNSNameView.as_view(),
         name='extradnsname'),
]
