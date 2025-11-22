from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User

parent_bp = Blueprint("parent_bp", __name__, url_prefix="/api/parent")


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


@parent_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid:
        return jsonify({"msg": "Invalid identity"}), 400
    user = User.query.get(uid)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    # expose safe fields
    return jsonify({
        "user": {
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": getattr(user, 'phone', None),
            "role": user.role.lower() if user.role else None
        }
    })


@parent_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid:
        return jsonify({"msg": "Invalid identity"}), 400
    user = User.query.get(uid)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json() or {}
    full_name = data.get('full_name')
    phone = data.get('phone')

    if full_name is not None:
        user.full_name = full_name.strip()
    if phone is not None:
        # basic normalization
        user.phone = phone.strip()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to save profile", "error": str(e)}), 500

    return jsonify({"message": "Profile updated", "user": {"user_id": user.id, "full_name": user.full_name, "phone": user.phone}})
