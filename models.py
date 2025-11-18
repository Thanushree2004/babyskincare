from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="parent")  # parent / doctor / admin
    phone = db.Column(db.String(20))
    profile_pic = db.Column(db.String(255))
    is_email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    babies = db.relationship("Baby", backref="parent", lazy=True)
    skin_records = db.relationship("SkinRecord", backref="creator", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)

    # Shared babies (doctor_side)
    shared_babies = db.relationship("DoctorShare", backref="doctor", foreign_keys="DoctorShare.doctor_id", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Baby(db.Model):
    __tablename__ = "babies"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skin_records = db.relationship("SkinRecord", backref="baby", lazy=True)
    doctor_shares = db.relationship("DoctorShare", backref="baby", lazy=True)


class RashType(db.Model):
    __tablename__ = "rash_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    care_tips = db.Column(db.Text)


class SkinRecord(db.Model):
    __tablename__ = "skin_records"

    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey("babies.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    predicted_rash_type = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("Comment", backref="record", lazy=True)
    consultations = db.relationship("Consultation", backref="record", lazy=True)
    shared_records = db.relationship("SharedRecord", backref="record", lazy=True)


# 🔥 Doctor–Parent Sharing Model (Enhanced)
class DoctorShare(db.Model):
    __tablename__ = "doctor_shares"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    baby_id = db.Column(db.Integer, db.ForeignKey("babies.id"), nullable=False)

    shared_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # parent/admin who shared
    permission = db.Column(db.String(20), default="view")            # view/comment/manage
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)

    shared_by = db.relationship("User", foreign_keys=[shared_by_id])


class SharedRecord(db.Model):
    __tablename__ = "shared_records"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("skin_records.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("skin_records.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("skin_records.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)


# 🔥 Audit Log — Transparency
class AccessLog(db.Model):
    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(30))
    target_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 🔔 Notifications (optional but recommended)
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    json_data = db.Column(db.JSON, nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
