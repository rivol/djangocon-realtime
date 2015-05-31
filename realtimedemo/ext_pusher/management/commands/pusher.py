from django.core.management.base import BaseCommand

from pusher import Pusher


class Command(BaseCommand):
    help = 'Sends a message with Pusher'

    def add_arguments(self, parser):
        parser.add_argument('message', nargs='+', type=str)

    def handle(self, *args, **options):
        message = ' '.join(options['message'])
        print(message)

        pusher = Pusher(
          app_id='121933',
          key='f1ebb516981a3315e492',
          secret='d9f31be884b8be02bcbc'
        )

        pusher.trigger('test_channel', 'my_event', {'message': message})
