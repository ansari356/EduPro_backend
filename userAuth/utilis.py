import shortuuid



# generate otp
def generate_otp(self):
    unique_key=shortuuid.uuid()
    otp_key=unique_key[:6]
    return otp_key