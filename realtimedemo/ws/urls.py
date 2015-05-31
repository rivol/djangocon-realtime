from django.conf.urls import patterns, url

from ws.views import WebSocketsMainView


urlpatterns = patterns('',
    url(r'^$', WebSocketsMainView.as_view(), name='ws_client'),
)
