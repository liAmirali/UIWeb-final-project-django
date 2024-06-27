from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

from .tokens import email_verification_token

User = get_user_model()

@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created and not instance.is_email_verified:
        current_site = get_current_site(None)
        mail_subject = 'Activate your account.'
        message = render_to_string('acc_active_email.html', {
            'user': instance,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(instance.pk)),
            'token': email_verification_token.make_token(instance),
        })
        send_mail(mail_subject, message, 'from@example.com', [instance.email])