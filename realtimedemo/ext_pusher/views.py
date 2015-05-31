from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from pusher import Pusher

from ext_pusher.forms import PusherForm


class PusherMainView(TemplateView):
    template_name = 'pusher.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if we have pusher credentials
        if not settings.PUSHER_APP_ID or not settings.PUSHER_KEY or not settings.PUSHER_SECRET:
            context['pusher_ready'] = False
        else:
            context['pusher_ready'] = True
            context['PUSHER_KEY'] = settings.PUSHER_KEY

        return context


class PusherSubmitView(FormView):
    form_class = PusherForm

    def form_valid(self, form):
        message = form.cleaned_data['message']

        pusher = Pusher(
          app_id=settings.PUSHER_APP_ID,
          key=settings.PUSHER_KEY,
          secret=settings.PUSHER_SECRET,
        )

        pusher.trigger('test_channel', 'my_event', {'message': message})

        return HttpResponse()
