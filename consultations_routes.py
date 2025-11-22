from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Consultation, User, Baby

consults_bp = Blueprint("consults_bp", __name__, url_prefix="/api/consultations")


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


@consults_bp.route('/book', methods=['POST'])
@jwt_required()
def book_consult():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    data = request.get_json() or {}
    parent_id = _safe_int(data.get('parent_id'))
    baby_id = _safe_int(data.get('baby_id'))
    doctor_id = _safe_int(data.get('doctor_id'))
    date = data.get('date')
    time = data.get('time')
    reason = data.get('reason')

    if not parent_id or uid != parent_id:
        return jsonify({"error": "Forbidden"}), 403
    if not baby_id or not doctor_id or not date or not time:
        return jsonify({"error": "Missing fields"}), 400

    # basic existence checks
    baby = Baby.query.get(baby_id)
    doc = User.query.get(doctor_id)
    if not baby or baby.parent_id != parent_id:
        return jsonify({"error": "Invalid baby"}), 400
    if not doc or (doc.role or '').lower() != 'doctor':
        return jsonify({"error": "Invalid doctor"}), 400

    try:
        c = Consultation(parent_id=parent_id, doctor_id=doctor_id, baby_id=baby_id, date=date, time=time, reason=reason)
        db.session.add(c)
        db.session.commit()
        return jsonify({"message": "Booked", "id": c.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to book", "details": str(e)}), 500


@consults_bp.route('/status/<int:user_id>', methods=['GET'])
@jwt_required()
def consult_status(user_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if uid != user_id:
        return jsonify({"error": "Forbidden"}), 403
    try:
        items = Consultation.query.filter((Consultation.parent_id == user_id) | (Consultation.doctor_id == user_id)).order_by(Consultation.created_at.desc()).all()
        out = []
        for c in items:
            out.append({
                "id": c.id,
                "parent_id": c.parent_id,
                "doctor_id": c.doctor_id,
                "baby_id": c.baby_id,
                "doctor_name": (c.doctor_id and User.query.get(c.doctor_id).full_name) or None,
                "baby_name": (c.baby_id and Baby.query.get(c.baby_id).name) or None,
                "date": c.date,
                "time": c.time,
                "reason": c.reason,
                "status": c.status,
                "created_at": c.created_at.isoformat()
            })
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": "Failed to load consultations", "details": str(e)}), 500


@consults_bp.route('/doctor', methods=['GET'])
@jwt_required()
def consults_for_doctor():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    try:
        items = Consultation.query.filter_by(doctor_id=uid).order_by(Consultation.created_at.desc()).all()
        out = []
        for c in items:
            out.append({
                "id": c.id,
                "consultation_id": c.id,
                "record_id": None,
                "baby_id": c.baby_id,
                "baby_name": (c.baby_id and Baby.query.get(c.baby_id).name) or None,
                "parent_id": c.parent_id,
                "requested_at": c.created_at.isoformat(),
                "rash_type": None,
                "status": c.status,
                "doctor_id": c.doctor_id
            })
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": "Failed to load" , "details": str(e)}), 500


@consults_bp.route('/<int:consult_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_consult(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404
    if c.parent_id != uid:
        return jsonify({"error": "Forbidden"}), 403
    if c.status != 'pending':
        return jsonify({"error": "Cannot cancel"}), 400
    try:
        c.status = 'cancelled'
        db.session.add(c)
        db.session.commit()
        return jsonify({"message": "Cancelled"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to cancel", "details": str(e)}), 500
