from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_email_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-verify')

def confirm_email_token(token, expiration=60*60*24):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-verify', max_age=expiration)
    except Exception:
        return None
    return email
