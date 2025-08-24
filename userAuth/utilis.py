import shortuuid
from django.conf import settings
from django.core.mail import send_mail


# generate otp
def generate_otp():
    unique_key=shortuuid.uuid()
    otp_key=unique_key[:6]
    return otp_key

# send email
def send_otp_email(email,otp):
    subject = "Password Reset OTP"
    message =f"Your OTP code is: {otp}. It will expire in 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)