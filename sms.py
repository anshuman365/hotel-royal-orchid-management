import pywhatkit as kit
import random
import datetime

otp = random.randint(100000, 999999)
message = f"Your Royal Orchid OTP is {otp}"

now = datetime.datetime.now()
kit.sendwhatmsg("+919876543210", message, now.hour, now.minute + 1)