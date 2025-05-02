from datetime import timedelta
from django.core.mail import EmailMessage
import random

import threading

from django.utils import timezone


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']]
        )
        EmailThread(email).start()


def return_date():
    now = timezone.now()
    return now + timedelta(days=1)


def generate_pk():
    number = random.randint(1000, 9999)
    return '{}{}'.format(timezone.now().strftime('%y%m%d'), number)