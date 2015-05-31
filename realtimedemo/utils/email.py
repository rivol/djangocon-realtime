import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


logger = logging.getLogger('utils.email')


def send_email(rcpt_email, email_subject, template_name, template_vars, from_email=None):
    logger.info("Sending %s to %s", template_name, rcpt_email)

    template_vars.update({
        'SITE_URL': settings.SITE_URL,
    })
    email_content = render_to_string(template_name, template_vars)

    # Send HTML-only email. Mandrill will automatically add the text variant.
    msg = EmailMessage(email_subject, email_content, from_email, [rcpt_email])
    msg.content_subtype = "html"
    msg.send()
