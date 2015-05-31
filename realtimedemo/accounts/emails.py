import logging
from django.conf import settings
from django.core.urlresolvers import reverse

from utils.email import send_email


logger = logging.getLogger('accounts.emails')


def send_password_reset(user, uid, token):
    try:
        email_subject = 'Django real-time demo password reset'
        confirm_reset_url = "%s%s" % (settings.SITE_URL,
                                      reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

        return send_email(user.email, email_subject, 'emails/password_reset.html', {
            'user': user,
            'confirm_reset_url': confirm_reset_url,
        })
    except:
        logger.exception("Couldn't send password reset to %s (%d)", user.email, user.id)
