import re
from utils.utils_require import MAX_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH

def validate_username(username):
    pattern = re.compile(r'[^a-zA-Z0-9_]')
    if re.match(pattern, username):
        return "[username] must contain only alphabets, digits, and underscores"
    if len(username) > MAX_USERNAME_LENGTH:
        return "Username must be at most 16 characters"
    return None

def validate_password(password):
    pattern = re.compile(r'[^a-zA-Z0-9]')
    if re.match(pattern, password):
        return "[password] can only contain alphabets and digits"
    if len(password) > MAX_PASSWORD_LENGTH or len(password) < MIN_PASSWORD_LENGTH:
        return "[password] length must be at least 8 and at most 16"
    return None

def validate_email(email):
    pattern = '^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$'
    if not re.match(pattern, email):
        return "[email] is not a valid email address"
    return None

def validate_phone_number(phone_number):
    pattern = re.compile(r'^[0-9]{11}$')
    if not re.match(pattern, phone_number):
        return "[phone_number] is not a valid 11-digit phone number"
    return None