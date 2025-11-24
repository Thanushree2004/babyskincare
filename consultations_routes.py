# consultations_routes.py
# Reference models.py path: c:\Users\thanu\OneDrive\Desktop\babyskincare\models.py

from flask import Blueprint, request, jsonify, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Consultation, User, Baby, SkinRecord, Conversation, Message
from werkzeug.utils import secure_filename
import os
import datetime
from sqlalchemy.exc import SQLAlchemyError

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
# GET SINGLE CONSULTATION DETAILS
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
        "doctor_notes": getattr(c, "doctor_notes", None),
        # provide a consumable URL for the frontend in addition to the raw filename
        "prescription_path": getattr(c, "prescription_path", None),
        "prescription_url": url_for('file', filename=getattr(c, "prescription_path", None), _external=False) if getattr(c, "prescription_path", None) else None,
        "created_at": c.created_at.isoformat(),
        "scan": scan_info
    })


# -------------------------------------------------------------
# SAVE DOCTOR NOTES (doctor only)
# -------------------------------------------------------------
@consults_bp.route('/<int:consult_id>/notes', methods=['PUT'])
@jwt_required()
def save_doctor_notes(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    data = request.get_json() or {}
    notes = data.get('doctor_notes', None)

    if notes is None:
        return jsonify({"error": "doctor_notes field required"}), 400

    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404

    # only assigned doctor can update notes
    if c.doctor_id != uid:
        return jsonify({"error": "Forbidden"}), 403

    try:
        c.doctor_notes = notes
        db.session.add(c)
        db.session.commit()
        return jsonify({"message": "Notes saved", "doctor_notes": c.doctor_notes})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save notes", "details": str(e)}), 500


# -------------------------------------------------------------
# UPLOAD PRESCRIPTION (doctor only) - accepts file field "prescription"
# -------------------------------------------------------------
@consults_bp.route('/<int:consult_id>/prescription', methods=['POST'])
@jwt_required()
def upload_prescription(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404

    # only assigned doctor can upload
    if c.doctor_id != uid:
        return jsonify({"error": "Forbidden"}), 403

    file = request.files.get("prescription")
    if not file:
        return jsonify({"error": "prescription file required"}), 400

    # ensure uploads path exists
    if not hasattr(current_app, "uploads_path"):
        return jsonify({"error": "Server misconfigured: uploads path missing"}), 500

    # secure filename and save
    fname = secure_filename(file.filename or "prescription")
    stem, ext = os.path.splitext(fname)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"{stem}_{ts}{ext or '.pdf'}"
    save_path = os.path.join(current_app.uploads_path, final_name)

    try:
        file.stream.seek(0)
        with open(save_path, "wb") as fh:
            fh.write(file.read())
    except Exception as e:
        current_app.logger.exception("Failed saving prescription")
        return jsonify({"error": "Failed to save file", "details": str(e)}), 500

    try:
        c.prescription_path = final_name
        db.session.add(c)
        db.session.commit()
        file_url = url_for('file', filename=final_name, _external=False)
        return jsonify({"message": "Uploaded", "prescription_url": file_url})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed saving record", "details": str(e)}), 500


# -------------------------------------------------------------
# CHAT: Get or create conversation, list messages for this consult
# GET  /api/consultations/<consult_id>/conversation
# POST /api/consultations/<consult_id>/conversation  { "text": "..." }
# -------------------------------------------------------------
def _get_or_create_conversation(consult_id, parent_id=None, doctor_id=None):
    """Return a conversation scoped to the consultation if possible.
    If a conversation for the consultation exists return it. Otherwise create one
    that references the consultation (and parent/doctor for lookup clarity).
    """
    if consult_id is None:
        return None

    # Primary attempt: find/create conversation scoped to the consultation_id.
    # This may fail if the DB schema hasn't been migrated to include consultation_id.
    try:
        conv = Conversation.query.filter_by(consultation_id=consult_id).first()
        if conv:
            return conv

        conv = Conversation(consultation_id=consult_id, parent_id=parent_id, doctor_id=doctor_id)
        db.session.add(conv)
        db.session.commit()
        return conv
    except SQLAlchemyError as e:
        # Migration might not be applied. Rollback and fallback to older behavior
        db.session.rollback()
        current_app.logger.warning("Conversation create by consultation_id failed — falling back to parent/doctor key (%s)", e)

    # Fallback: find/create conversation by parent+doctor pair (legacy behavior)
    try:
        conv = Conversation.query.filter_by(parent_id=parent_id, doctor_id=doctor_id).first()
        if conv:
            return conv
        conv = Conversation(parent_id=parent_id, doctor_id=doctor_id)
        db.session.add(conv)
        db.session.commit()
        return conv
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to create conversation (fallback): %s", e)
        return None


@consults_bp.route('/<int:consult_id>/conversation', methods=['GET'])
@jwt_required()
def get_conversation(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404

    # only parent or doctor can view
    if uid not in (c.parent_id, c.doctor_id):
        return jsonify({"error": "Forbidden"}), 403

    conv = _get_or_create_conversation(consult_id, c.parent_id, c.doctor_id)
    if not conv:
        return jsonify({"conversation_id": None, "messages": []})

    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.asc()).all()
    out = []
    for m in messages:
        out.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "text": m.text,
            "read": m.read,
            "created_at": m.created_at.isoformat()
        })

    return jsonify({"conversation_id": conv.id, "messages": out})


@consults_bp.route('/<int:consult_id>/conversation', methods=['POST'])
@jwt_required()
def post_message(consult_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)

    c = Consultation.query.get(consult_id)
    if not c:
        return jsonify({"error": "Not found"}), 404

    if uid not in (c.parent_id, c.doctor_id):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400

    conv = _get_or_create_conversation(consult_id, c.parent_id, c.doctor_id)
    if not conv:
        return jsonify({"error": "Failed to create conversation"}), 500

    try:
        m = Message(conversation_id=conv.id, sender_id=uid, text=text)
        db.session.add(m)
        db.session.commit()
        return jsonify({
            "message": "Sent",
            "id": m.id,
            "sender_id": m.sender_id,
            "text": m.text,
            "created_at": m.created_at.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to send", "details": str(e)}), 500
