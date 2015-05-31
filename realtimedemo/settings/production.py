from settings.base import *


DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['djangocon.thorgate.eu']

# Static site url, used when we need absolute url but lack request object, e.g. in email sending.
SITE_URL = 'http://djangocon.thorgate.eu'
WEBSOCKET_URL = 'ws://ws.djangocon.thorgate.eu'

EMAIL_HOST_PASSWORD = 'TODO (api key)'


STATIC_URL = '/assets/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'realtimedemo',
    }
}

# Production logging - all INFO and higher messages go to info.log file. ERROR and higher messages additionally go to
#  error.log file plus by email to admins.
LOGGING['handlers'] = {
    'info_log': {
        'level': 'INFO',
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': '/var/log/realtimedemo/info.log',
        'formatter': 'default',
    },
    'error_log': {
        'level': 'ERROR',
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': '/var/log/realtimedemo/error.log',
        'formatter': 'default',
    },
    'mail_admins': {
        'level': 'ERROR',
        'class': 'django.utils.log.AdminEmailHandler',
        'formatter': 'default',
        'filters': ['require_debug_false'],
    },
}
LOGGING['loggers'][''] = {
    'handlers': ['info_log', 'error_log', 'mail_admins'],
    'level': 'INFO',
    'filters': ['require_debug_false'],
}
