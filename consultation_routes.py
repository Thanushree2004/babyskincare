from flask import Blueprint, request, jsonify
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Consultation, SkinRecord, Baby

consult_bp = Blueprint("consult_bp", __name__, url_prefix="/api/consultations")


# ---------------------------------------------------------
# 1️⃣ Parent Sends Consultation Request
# ---------------------------------------------------------
@consult_bp.route("/request", methods=["POST"])
@jwt_required()
def request_consultation():
    data = request.get_json() or {}

    record_id = data.get("record_id")
    doctor_id = data.get("doctor_id")
    parent_id = get_jwt_identity()

    if not record_id or not doctor_id:
        return jsonify({"error": "record_id and doctor_id required"}), 400

    # Validate skin record
    record = SkinRecord.query.filter_by(id=record_id).first()
    if not record:
        return jsonify({"error": "Skin record not found"}), 404

    # Validate doctor
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # Create consultation request
    consultation = Consultation(
        record_id=record_id,
        doctor_id=doctor_id,
        parent_id=parent_id,
        status="pending"
    )

    db.session.add(consultation)
    db.session.commit()

    return jsonify({"message": "Consultation request sent successfully!"}), 201


# ---------------------------------------------------------
# 2️⃣ Doctor Views Consultation Requests
# ---------------------------------------------------------
@consult_bp.route("/doctor", methods=["GET"])
@jwt_required()
def doctor_requests():
    doctor_id = get_jwt_identity()

    # Check if user is doctor
    doctor = User.query.get(doctor_id)
    if not doctor or doctor.role != "doctor":
        return jsonify({"error": "Access restricted to doctors only"}), 403

    requests = (
        Consultation.query.filter_by(doctor_id=doctor_id)
        .order_by(Consultation.requested_at.desc())
        .all()
    )

    response = []
    for req in requests:
        record = SkinRecord.query.get(req.record_id)
        baby = Baby.query.get(record.baby_id)

        response.append({
            "consultation_id": req.id,
            "status": req.status,
            "baby_name": baby.name,
            "rash_type": record.predicted_rash_type,
            "requested_at": req.requested_at.strftime("%Y-%m-%d %H:%M"),
            "record_id": record.id
        })

    return jsonify(response), 200


# ---------------------------------------------------------
# 3️⃣ Doctor Accepts or Rejects Consultation Request
# ---------------------------------------------------------
@consult_bp.route("/<int:consult_id>/update", methods=["PUT"])
@jwt_required()
def update_consultation(consult_id):
    data = request.get_json() or {}
    doctor_id = get_jwt_identity()

    status = data.get("status")
    if status not in ["accepted", "rejected"]:
        return jsonify({"error": "Invalid status. Use 'accepted' or 'rejected'"}), 400

    consultation = Consultation.query.get(consult_id)
    if not consultation:
        return jsonify({"error": "Consultation not found"}), 404

    # Doctor access only
    if consultation.doctor_id != doctor_id:
        return jsonify({"error": "Not authorized"}), 403

    consultation.status = status
    db.session.commit()

    return jsonify({"message": f"Consultation {status} successfully!"}), 200


# ---------------------------------------------------------
# 4️⃣ Parent Views All Their Consultation Requests
# ---------------------------------------------------------
@consult_bp.route("/parent", methods=["GET"])
@jwt_required()
def parent_consultations():
    parent_id = get_jwt_identity()

    requests = Consultation.query.filter_by(parent_id=parent_id).order_by(
        Consultation.requested_at.desc()
    ).all()

    output = []
    for req in requests:
        doctor = User.query.get(req.doctor_id)

        output.append({
            "consultation_id": req.id,
            "doctor_name": doctor.full_name,
            "status": req.status,
            "requested_at": req.requested_at.strftime("%Y-%m-%d %H:%M"),
            "record_id": req.record_id
        })

    return jsonify(output), 200


# ---------------------------------------------------------
# 5️⃣ Doctor Gets Full Baby Record After Accepting
# ---------------------------------------------------------
@consult_bp.route("/details/<int:record_id>", methods=["GET"])
@jwt_required()
def consultation_details(record_id):
    doctor_id = get_jwt_identity()

    # Verify doctor has access
    consultation = Consultation.query.filter_by(
        record_id=record_id,
        doctor_id=doctor_id,
        status="accepted"
    ).first()

    if not consultation:
        return jsonify({"error": "Access denied"}), 403

    record = SkinRecord.query.get(record_id)
    baby = Baby.query.get(record.baby_id)

    return jsonify({
        "baby_name": baby.name,
        "rash_type": record.predicted_rash_type,
        "confidence": record.confidence_score,
        "image_url": record.image_path,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M")
    }), 200
