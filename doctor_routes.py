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
    doctor = User.query.filter_by(id=user_id, role="doctor").first()

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    return jsonify({
        "id": doctor.id,
        "full_name": doctor.full_name,
        "email": doctor.email,
        "phone": doctor.phone,
        "profile_pic": doctor.profile_pic,
        "specialization": doctor.role,  
        "created_at": doctor.created_at.strftime("%Y-%m-%d"),
    }), 200


# ---------------------------------------------------------
# UPDATE Doctor Profile
# ---------------------------------------------------------
@doctor_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    doctor = User.query.filter_by(id=user_id, role="doctor").first()

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data = request.get_json()

    doctor.full_name = data.get("full_name", doctor.full_name)
    doctor.phone = data.get("phone", doctor.phone)
    doctor.email = data.get("email", doctor.email)

    db.session.commit()

    return jsonify({"message": "Profile updated successfully!"}), 200
