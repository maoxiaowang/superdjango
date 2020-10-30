"""
https://docs.djangoproject.com/en/1.11/topics/email/
"""
from django.conf import settings
from django.core import mail
from django.core.mail import get_connection, EmailMultiAlternatives, send_mail
from django.shortcuts import render
from django.utils.safestring import mark_safe

__all__ = [
    'send_mail',
    'EmailMultiAlternatives'
]


# def send_mail_by_default(subject, message, recipient_list,
#                          fail_silently=False, html_message=None, connection=None):
#     """
#     Send mail using account set in settings.py
#     """
#     if isinstance(recipient_list, str):
#         recipient_list = [recipient_list]
#     connection = connection or get_connection(
#         fail_silently=fail_silently,
#     )
#     mail = EmailMultiAlternatives(subject, message, to=recipient_list, connection=connection)
#     if html_message:
#         mail.attach_alternative(html_message, 'text/html')
#
#     return mail.send()

def send_mail_by_default(subject, message, recipient_list, bcc=None, cc=None,
                         content_type='html', **kwargs):
    assert content_type in ('html', 'plain')

    # 防止被认为垃圾邮件（163邮箱）
    default_cc = [settings.DEFAULT_FROM_EMAIL]
    if cc:
        assert isinstance(cc, list)
        default_cc.extend(cc)
    email = mail.EmailMessage(
        subject,
        message,
        to=recipient_list,
        cc=default_cc,
        bcc=bcc,
        **kwargs
    )
    setattr(email, 'content_subtype', content_type)
    email.send()


# def test_send_text(recipient_list):
#     send_mail_by_default('text test title', 'This is a test email.', recipient_list)


# def test_send_html(recipient_list):
#     html_content = render(
#         None, 'mail/general_mail.html',
#         {'subject': 'html test title',
#          'content': mark_safe('<p style="color:red">This is a test email.</p>')}).content.decode('utf-8')
#     send_mail_by_default(
#         'html_test',
#         'html',
#         recipient_list,
#         html_message=html_content,
#     )
