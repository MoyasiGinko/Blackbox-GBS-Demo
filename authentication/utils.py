from django.core.mail import send_mail
import os


def send_email(subject, recipient_list, message):
  print("Sending email...")
  from_email = os.environ.get('EMAIL_HOST_USER')
  password = os.environ.get('EMAIL_HOST_PASSWORD')
  print('the email host user is:', from_email)
  print('the email host password is:', password)
  if not from_email:
    raise ValueError("EMAIL_HOST_USER environment variable is not set")
  
  if not recipient_list:
    raise ValueError("Recipient list is empty")
  
  try:
    send_mail(
      subject=subject,
      message=message,
      from_email=None,
      recipient_list=recipient_list,
      fail_silently=False,
    )
  except Exception as e:
    raise RuntimeError(f"Failed to send email: {e}")