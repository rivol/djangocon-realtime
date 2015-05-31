from django.conf.urls import patterns, url

from ext_pusher.views import PusherMainView, PusherSubmitView

urlpatterns = patterns('',
    url(r'^$', PusherMainView.as_view(), name='pusher_client'),
    url(r'^submit/$', PusherSubmitView.as_view(), name='pusher_submit'),
)
