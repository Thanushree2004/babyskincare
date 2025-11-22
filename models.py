# filepath: c:\Users\thanu\OneDrive\Desktop\babyskincare\models.py
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# ============================
# USER MODEL (PARENT / DOCTOR)
# ============================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # role = parent / doctor
    role = db.Column(db.String(20), nullable=False, default="parent")

    # contact phone number (optional)
    phone = db.Column(db.String(30))

    # doctor-specific fields
    specialization = db.Column(db.String(120))
    experience = db.Column(db.Integer)
    bio = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ========================
    # PASSWORD HELPERS
    # ========================
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ================================
# BABY MODEL
# ================================
class Baby(db.Model):
    __tablename__ = "babies"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.String(20))

    parent = db.relationship("User", backref="babies")


# ================================
# SKIN RECORD (used by predict_routes)
# ================================
class SkinRecord(db.Model):
    __tablename__ = "skin_records"

    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey("babies.id"), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    predicted_rash_type = db.Column(db.String(120))
    confidence_score = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    baby = db.relationship("Baby", backref="skin_records")
    created_by = db.relationship("User", backref="created_records", foreign_keys=[created_by_id])


# ================================
# RASH TYPES / CARE TIPS
# ================================
class RashType(db.Model):
    __tablename__ = "rash_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    care_tips = db.Column(db.Text)


# ================================
# DOCTOR SHARES / COMMENTS
# ================================
class DoctorShare(db.Model):
    __tablename__ = "doctor_shares"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    baby_id = db.Column(db.Integer, db.ForeignKey("babies.id"))
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("skin_records.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================
# CONSULTATION REQUEST
# ================================
class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)

    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    baby_id = db.Column(db.Integer, db.ForeignKey("babies.id"))

    date = db.Column(db.String(30))
    time = db.Column(db.String(30))
    reason = db.Column(db.Text)

    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ...existing code...
class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", backref="conversation", cascade="all, delete-orphan")

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"))
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    text = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# ...existing code...