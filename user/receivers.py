from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

from django.conf import settings

from .tokens import email_verification_token

User = get_user_model()


@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created and not instance.is_superuser and not instance.is_email_verified:
        domain = settings.SITE_DOMAIN
        mail_subject = 'Activate your account.'
        message = render_to_string('user/acc_active_email.html', {
            'user': instance,
            'domain': domain,
            'uidb64': urlsafe_base64_encode(force_bytes(instance.pk)),
            'token': email_verification_token.make_token(instance),
        })
        send_mail(subject=mail_subject, html_message=message, message=message,
                  from_email="objectmanager@gmail.com", recipient_list=[instance.email])
