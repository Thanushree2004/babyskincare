from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User

doctors_bp = Blueprint("doctors_bp", __name__, url_prefix="/api/doctors")


@doctors_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_doctors():
    try:
        docs = User.query.filter((User.role == 'doctor') | (User.role == 'Doctor')).all()
        out = []
        for d in docs:
            out.append({
                "id": d.id,
                "first_name": (d.full_name or '').split(' ')[0] if d.full_name else '',
                "last_name": ' '.join((d.full_name or '').split(' ')[1:]) if d.full_name and len((d.full_name or '').split(' '))>1 else '',
                "full_name": d.full_name,
                "email": d.email,
                "phone": getattr(d, 'phone', None),
                "specialization": d.specialization,
                "experience": d.experience,
                "bio": d.bio
            })
        return jsonify(out)
    except Exception:
        return jsonify({"error": "Failed to list doctors"}), 500


@doctors_bp.route("/<int:doc_id>", methods=["GET"])
@jwt_required(optional=True)
def get_doctor(doc_id):
    d = User.query.get(doc_id)
    if not d or (d.role or '').lower() != 'doctor':
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": d.id,
        "first_name": (d.full_name or '').split(' ')[0] if d.full_name else '',
        "last_name": ' '.join((d.full_name or '').split(' ')[1:]) if d.full_name and len((d.full_name or '').split(' '))>1 else '',
        "full_name": d.full_name,
        "email": d.email,
        "phone": getattr(d, 'phone', None),
        "specialization": d.specialization,
        "experience": d.experience,
        "bio": d.bio
    })
