from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Baby, SkinRecord

babies_bp = Blueprint("babies_bp", __name__, url_prefix="/api/babies")


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


@babies_bp.route("/<int:parent_id>", methods=["GET"])
@jwt_required()
def list_babies(parent_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid or uid != parent_id:
        return jsonify({"error": "Forbidden"}), 403
    try:
        items = Baby.query.filter_by(parent_id=parent_id).all()
        out = []
        for b in items:
            out.append({
                "id": b.id,
                "name": b.name,
                "date_of_birth": b.date_of_birth
            })
        return jsonify(out)
    except Exception:
        return jsonify({"error": "Failed to list babies"}), 500


@babies_bp.route("", methods=["POST"])
@jwt_required()
def create_baby():
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid:
        return jsonify({"error": "Invalid identity"}), 400
    data = request.get_json() or {}
    name = data.get("name")
    dob = data.get("date_of_birth")
    parent_id = data.get("parent_id")
    if parent_id is not None:
        parent_id = _safe_int(parent_id)
    if parent_id and parent_id != uid:
        return jsonify({"error": "Forbidden"}), 403
    parent_id = uid

    if not name or not str(name).strip():
        return jsonify({"error": "Missing baby name"}), 400

    try:
        baby = Baby(parent_id=parent_id, name=name.strip(), date_of_birth=(dob or None))
        db.session.add(baby)
        db.session.commit()
        return jsonify({"id": baby.id, "name": baby.name, "date_of_birth": baby.date_of_birth}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create baby", "details": str(e)}), 500


@babies_bp.route("/<int:parent_id>/<int:baby_id>/history", methods=["GET"])
@jwt_required()
def baby_history(parent_id, baby_id):
    uid = get_jwt_identity()
    uid = _safe_int(uid)
    if not uid or uid != parent_id:
        return jsonify({"error": "Forbidden"}), 403
    baby = Baby.query.get(baby_id)
    if not baby or baby.parent_id != parent_id:
        return jsonify({"error": "Not found"}), 404
    try:
        scans = SkinRecord.query.filter_by(baby_id=baby_id).order_by(SkinRecord.created_at.desc()).all()
        out_scans = []
        for s in scans:
            out_scans.append({
                "id": s.id,
                "rash_type": s.predicted_rash_type,
                "confidence": s.confidence_score,
                "image_url": url_for("file", filename=s.image_path, _external=False) if s.image_path else None,
                "created_at": s.created_at.isoformat()
            })
        return jsonify({"baby": {"id": baby.id, "name": baby.name, "date_of_birth": baby.date_of_birth}, "scans": out_scans})
    except Exception:
        return jsonify({"error": "Failed to load history"}), 500
