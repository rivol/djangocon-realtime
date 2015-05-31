from django.conf import settings
from django.views.generic.base import TemplateView


class WebSocketsMainView(TemplateView):
    template_name = 'websocket.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['WEBSOCKET_URL'] = settings.WEBSOCKET_URL
        return context
