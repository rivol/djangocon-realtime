from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView


admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('accounts.urls')),
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),

    url(r'^pusher/', include('ext_pusher.urls')),
    url(r'^websocket/', include('ws.urls')),

    url(r'^tagauks/', include(admin.site.urls)),
)
