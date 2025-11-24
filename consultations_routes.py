from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Consultation, User, Baby, SkinRecord

consults_bp = Blueprint("consults_bp", __name__, url_prefix="/api/consultations")


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


# -------------------------------------------------------------
# BOOK CONSULTATION
# -------------------------------------------------------------
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

    baby = Baby.query.get(baby_id)
    doc = User.query.get(doctor_id)
    if not baby or baby.parent_id != parent_id:
        return jsonify({"error": "Invalid baby"}), 400
    if not doc or (doc.role or '').lower() != 'doctor':
        return jsonify({"error": "Invalid doctor"}), 400

    try:
        c = Consultation(parent_id=parent_id, doctor_id=doctor_id, baby_id=baby_id,
                         date=date, time=time, reason=reason)
        db.session.add(c)
        db.session.commit()

        scan_id = data.get('scan_id') or data.get('record_id')
        scan = None
        try:
            if scan_id:
                scan = SkinRecord.query.get(int(scan_id)) if str(scan_id).isdigit() else None
                if scan and scan.baby_id != baby_id:
                    scan = None
            if not scan:
                scan = SkinRecord.query.filter_by(baby_id=baby_id).order_by(SkinRecord.created_at.desc()).first()
        except Exception:
            scan = None

        scan_info = None
        if scan:
            scan_info = {
                'id': scan.id,
                'image_url': url_for('file', filename=scan.image_path, _external=False),
                'rash_type': scan.predicted_rash_type,
                'confidence': scan.confidence_score,
                'created_at': scan.created_at.isoformat()
            }

        return jsonify({"message": "Booked", "id": c.id, "scan": scan_info}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to book", "details": str(e)}), 500


# -------------------------------------------------------------
# PARENT OR DOCTOR CONSULTATION STATUS
# -------------------------------------------------------------
@consults_bp.route('/status/<int:user_id>', methods=['GET'])
@jwt_required()
def consult_status(user_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if uid != user_id:
        return jsonify({"error": "Forbidden"}), 403

    try:
        items = Consultation.query.filter(
            (Consultation.parent_id == user_id) |
            (Consultation.doctor_id == user_id)
        ).order_by(Consultation.created_at.desc()).all()

        out = []
        for c in items:
            scan = None
            try:
                if c.baby_id:
                    scan = SkinRecord.query.filter_by(baby_id=c.baby_id)\
                            .order_by(SkinRecord.created_at.desc()).first()
            except Exception:
                scan = None

            scan_info = None
            if scan:
                scan_info = {
                    'id': scan.id,
                    'image_url': url_for('file', filename=scan.image_path, _external=False),
                    'rash_type': scan.predicted_rash_type,
                    'confidence': scan.confidence_score,
                    'created_at': scan.created_at.isoformat()
                }

            out.append({
                "id": c.id,
                "parent_id": c.parent_id,
                "doctor_id": c.doctor_id,
                "baby_id": c.baby_id,
                "doctor_name": User.query.get(c.doctor_id).full_name if c.doctor_id else None,
                "baby_name": Baby.query.get(c.baby_id).name if c.baby_id else None,
                "date": c.date,
                "time": c.time,
                "reason": c.reason,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "scan": scan_info
            })

        return jsonify(out)

    except Exception as e:
        return jsonify({"error": "Failed to load consultations", "details": str(e)}), 500


# -------------------------------------------------------------
# DOCTOR'S CONSULTATIONS LIST
# -------------------------------------------------------------
@consults_bp.route('/doctor', methods=['GET'])
@jwt_required()
def consults_for_doctor():
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    try:
        items = Consultation.query.filter_by(doctor_id=uid)\
                .order_by(Consultation.created_at.desc()).all()

        out = []
        for c in items:
            scan = None
            try:
                if c.baby_id:
                    scan = SkinRecord.query.filter_by(baby_id=c.baby_id)\
                            .order_by(SkinRecord.created_at.desc()).first()
            except Exception:
                scan = None

            scan_info = None
            if scan:
                scan_info = {
                    'id': scan.id,
                    'image_url': url_for('file', filename=scan.image_path, _external=False),
                    'rash_type': scan.predicted_rash_type,
                    'confidence': scan.confidence_score,
                    'created_at': scan.created_at.isoformat()
                }

            out.append({
                "id": c.id,
                "consultation_id": c.id,
                "record_id": scan.id if scan else None,
                "baby_id": c.baby_id,
                "baby_name": Baby.query.get(c.baby_id).name if c.baby_id else None,
                "parent_id": c.parent_id,
                "requested_at": c.created_at.isoformat(),
                "rash_type": scan.predicted_rash_type if scan else None,
                "status": c.status,
                "doctor_id": c.doctor_id,
                "scan": scan_info
            })

        return jsonify(out)

    except Exception as e:
        return jsonify({"error": "Failed to load", "details": str(e)}), 500


# -------------------------------------------------------------
# CANCEL CONSULT
# -------------------------------------------------------------
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


# -------------------------------------------------------------
# UPDATE STATUS (ACCEPT / REJECT / SCHEDULE)
# -------------------------------------------------------------
@consults_bp.route('/<int:consult_id>/status', methods=['PUT'])
@jwt_required()
def update_consult_status(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    data = request.get_json() or {}
    new_status = (data.get('status') or '').lower()
    allowed = {'accepted', 'rejected', 'scheduled', 'cancelled'}

    if new_status not in allowed:
        return jsonify({"error": "Invalid status"}), 400

    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404

    if c.doctor_id != uid:
        return jsonify({"error": "Forbidden"}), 403

    try:
        c.status = new_status
        db.session.add(c)
        db.session.commit()
        return jsonify({"message": "Status updated", "status": c.status})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update status", "details": str(e)}), 500


# -------------------------------------------------------------
# NEW ROUTE: GET SINGLE CONSULTATION DETAILS
# -------------------------------------------------------------
@consults_bp.route('/<int:consult_id>', methods=['GET'])
@jwt_required()
def get_consultation(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404

    # Allow parent or doctor to view
    if uid not in (c.parent_id, c.doctor_id):
        return jsonify({"error": "Forbidden"}), 403

    scan = None
    try:
        if c.baby_id:
            scan = SkinRecord.query.filter_by(baby_id=c.baby_id)\
                    .order_by(SkinRecord.created_at.desc()).first()
    except Exception:
        scan = None

    scan_info = None
    if scan:
        scan_info = {
            'id': scan.id,
            'image_url': url_for('file', filename=scan.image_path, _external=False),
            'rash_type': scan.predicted_rash_type,
            'confidence': scan.confidence_score,
            'created_at': scan.created_at.isoformat()
        }

    return jsonify({
        "id": c.id,
        "parent_id": c.parent_id,
        "parent_name": User.query.get(c.parent_id).full_name if c.parent_id else None,
        "doctor_id": c.doctor_id,
        "doctor_name": User.query.get(c.doctor_id).full_name if c.doctor_id else None,
        "baby_id": c.baby_id,
        "baby_name": Baby.query.get(c.baby_id).name if c.baby_id else None,
        "date": c.date,
        "time": c.time,
        "reason": c.reason,
        "status": c.status,
        "created_at": c.created_at.isoformat(),
        "scan": scan_info
    })
