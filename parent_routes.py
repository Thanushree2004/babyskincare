from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Baby, SkinRecord, Consultation, User

parent_bp = Blueprint("parent_bp", __name__, url_prefix="/api/parent")


@parent_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user_id = int(identity)
    except Exception:
        return jsonify({"error": "Invalid identity"}), 401

    user = User.query.filter(User.id == user_id, User.role.in_(["parent", "Parent"])) .first()
    if not user:
        return jsonify({"error": "Profile not found"}), 404

    profile = {"id": user.id, "full_name": user.full_name, "email": user.email}
    # include any doctor-like fields if present (safe access)
    if hasattr(user, 'phone'):
        profile['phone'] = getattr(user, 'phone')

    return jsonify({"user": profile}), 200


@parent_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user_id = int(identity)
    except Exception:
        return jsonify({"error": "Invalid identity"}), 401

    user = User.query.filter(User.id == user_id, User.role.in_(["parent", "Parent"])) .first()
    if not user:
        return jsonify({"error": "Profile not found"}), 404

    data = request.get_json() or {}
    # update allowed fields safely
    if 'full_name' in data:
        user.full_name = data.get('full_name') or user.full_name
    if 'email' in data:
        user.email = data.get('email') or user.email
    # accept phone but only set if column exists
    if 'phone' in data and hasattr(User, 'phone'):
        try:
            setattr(user, 'phone', data.get('phone'))
        except Exception:
            pass

    db.session.commit()
    return jsonify({"message": "Profile saved"}), 200



@parent_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = int(identity)

    babies = Baby.query.filter_by(parent_id=user_id).all()
    babies_data = [{"id": b.id, "name": b.name, "dob": b.date_of_birth} for b in babies]

    consultations = (Consultation.query
                     .filter(Consultation.parent_id == user_id)
                     .order_by(Consultation.created_at.desc())
                     .limit(10).all())
    cons = [{"id": c.id, "doctor_id": c.doctor_id, "baby_id": c.baby_id,
             "status": c.status, "date": c.date, "time": c.time} for c in consultations]

    return jsonify({"babies": babies_data, "consultations": cons}), 200


@parent_bp.route("/babies/<int:baby_id>/history", methods=["GET"])
@jwt_required()
def baby_history(baby_id):
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = int(identity)

    baby = Baby.query.get_or_404(baby_id)
    if baby.parent_id != user_id:
        return jsonify({"error": "forbidden"}), 403

    records = SkinRecord.query.filter_by(baby_id=baby_id).order_by(SkinRecord.created_at.desc()).all()
    data = [{"id": r.id, "rash": r.predicted_rash_type, "confidence": r.confidence_score,
             "image": r.image_path, "created_at": r.created_at.isoformat()} for r in records]
    return jsonify({"history": data}), 200


@parent_bp.route("/doctors", methods=["GET"])
@jwt_required(optional=True)
def doctors_list():
    # optional auth: we don't need the user id, but accept if present
    identity = get_jwt_identity()
    if identity is not None:
        try:
            _ = int(identity)
        except Exception:
            pass

    docs = User.query.filter_by(role="doctor").all()
    data = [{"id": d.id, "full_name": d.full_name, "specialization": d.specialization} for d in docs]
    return jsonify({"doctors": data}), 200


@parent_bp.route("/doctors/<int:doc_id>", methods=["GET"])
@jwt_required(optional=True)
def doctor_profile(doc_id):
    identity = get_jwt_identity()
    if identity is not None:
        try:
            _ = int(identity)
        except Exception:
            pass

    doc = User.query.filter_by(id=doc_id, role="doctor").first_or_404()
    profile = {"id": doc.id, "full_name": doc.full_name, "specialization": doc.specialization,
               "bio": doc.bio, "experience": doc.experience}
    return jsonify({"doctor": profile}), 200


@parent_bp.route("/consultations/book", methods=["POST"])
@jwt_required()
def book_consultation():
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = int(identity)

    data = request.get_json() or {}
    baby_id = data.get("baby_id")
    doctor_id = data.get("doctor_id")
    date = data.get("date")
    time = data.get("time")
    reason = data.get("reason", "")

    if not all([baby_id, doctor_id, date, time]):
        return jsonify({"error": "baby_id, doctor_id, date and time required"}), 400

    # ensure baby belongs to requesting parent
    baby = Baby.query.get(baby_id)
    if not baby or baby.parent_id != user_id:
        return jsonify({"error": "invalid baby_id or not authorized for this baby"}), 403

    cons = Consultation(parent_id=user_id, doctor_id=doctor_id, baby_id=baby_id,
                        date=date, time=time, reason=reason)
    db.session.add(cons)
    db.session.commit()
    return jsonify({"message": "Consultation requested", "consultation_id": cons.id}), 201


@parent_bp.route("/consultations/<int:consult_id>/status", methods=["GET"])
@jwt_required()
def consult_status(consult_id):
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = int(identity)

    c = Consultation.query.get_or_404(consult_id)
    if c.parent_id != user_id and c.doctor_id != user_id:
        return jsonify({"error": "forbidden"}), 403
    return jsonify({"id": c.id, "status": c.status, "date": c.date, "time": c.time}), 200