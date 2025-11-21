from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User

doctor_bp = Blueprint("doctor_bp", __name__, url_prefix="/api/doctor")


# ---------------------------------------------------------
# GET Doctor Profile
# ---------------------------------------------------------
@doctor_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    # role in DB may be capitalized
    doctor = User.query.filter(User.id == user_id, User.role.in_(["doctor", "Doctor"])) .first()

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    return jsonify({
        "id": doctor.id,
        "full_name": doctor.full_name,
        "email": doctor.email,
        "role": doctor.role.lower() if doctor.role else "doctor",
        "specialization": getattr(doctor, "specialization", None),
        "experience": getattr(doctor, "experience", None),
        "bio": getattr(doctor, "bio", None),
        "created_at": doctor.created_at.strftime("%Y-%m-%d"),
    }), 200


# ---------------------------------------------------------
# UPDATE Doctor Profile
# ---------------------------------------------------------
@doctor_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    doctor = User.query.filter(User.id == user_id, User.role.in_(["doctor", "Doctor"])) .first()

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data = request.get_json() or {}

    doctor.full_name = data.get("full_name", doctor.full_name)
    doctor.email = data.get("email", doctor.email)
    if "specialization" in data:
        doctor.specialization = data.get("specialization")
    if "experience" in data:
        try:
            doctor.experience = int(data.get("experience")) if data.get("experience") is not None else doctor.experience
        except (TypeError, ValueError):
            return jsonify({"error": "experience must be an integer"}), 400
    if "bio" in data:
        doctor.bio = data.get("bio")

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully!",
        "profile": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "role": doctor.role.lower() if doctor.role else "doctor",
            "specialization": getattr(doctor, "specialization", None),
            "experience": getattr(doctor, "experience", None),
            "bio": getattr(doctor, "bio", None)
        }
    }), 200
