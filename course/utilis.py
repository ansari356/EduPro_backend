import random
import string

def genrate_coupon_code(length=10):
    characters = string.ascii_uppercase + string.digits 
    coupon_code = ''.join(random.choice(characters) for _ in range(length))
    return coupon_code
