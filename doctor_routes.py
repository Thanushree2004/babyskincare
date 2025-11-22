from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User

doctor_bp = Blueprint("doctor_bp", __name__, url_prefix="/api/doctor")


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


@doctor_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid:
        return jsonify({"error": "Invalid identity"}), 400
    user = User.query.get(uid)
    if not user or (user.role or '').lower() != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "id": user.id,
        "first_name": user.full_name.split(' ')[0] if user.full_name else '',
        "last_name": ' '.join(user.full_name.split(' ')[1:]) if user.full_name and len(user.full_name.split(' '))>1 else '',
        "specialization": user.specialization,
        "experience": user.experience,
        "bio": user.bio
    })


@doctor_bp.route("/profile", methods=["PUT"])
@jwt_required()
def put_profile():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid:
        return jsonify({"error": "Invalid identity"}), 400
    user = User.query.get(uid)
    if not user or (user.role or '').lower() != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    first = data.get('first_name')
    last = data.get('last_name')
    specialization = data.get('specialization')
    experience = data.get('experience')
    bio = data.get('bio')

    if first is not None or last is not None:
        # combine into full_name
        f = (first or '').strip()
        l = (last or '').strip()
        user.full_name = (f + (' ' + l if l else '')).strip() or user.full_name
    if specialization is not None:
        user.specialization = specialization.strip()
    if experience is not None:
        try:
            user.experience = int(experience)
        except Exception:
            pass
    if bio is not None:
        user.bio = bio

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save", "details": str(e)}), 500

    return jsonify({"message": "Profile updated", "user": {"id": user.id, "full_name": user.full_name, "specialization": user.specialization, "experience": user.experience, "bio": user.bio}})
