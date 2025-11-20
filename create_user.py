from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

# EDIT to match the email/password you will use on the login page
EMAIL = "thanushreesk04@gmail.com"
PASSWORD = "1234"
FULL_NAME = "Test Parent"

app = create_app()

with app.app_context():
    db.create_all()
    existing = User.query.filter_by(email=EMAIL).first()
    if existing:
        print(f"User already exists: id={existing.id}, email={existing.email}")
    else:
        user = User(full_name=FULL_NAME, email=EMAIL)
        # prefer model helper if available
        try:
            user.set_password(PASSWORD)
        except AttributeError:
            user.password_hash = generate_password_hash(PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"Created user id={user.id}, email={user.email}")