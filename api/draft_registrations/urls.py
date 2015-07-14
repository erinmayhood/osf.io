from django.conf.urls import url
from api.draft_registrations import views

urlpatterns = [
    url(r'^$', views.DraftRegistrationList.as_view(), name='registration-list'),
    url(r'^(?P<token>\w+)/$', views.RegistrationCreateWithToken.as_view(), name='registration-create'),
    url(r'^(?P<draft_id>\w+)/$', views.DraftRegistrationDetail.as_view(), name='registration-detail'),

]
