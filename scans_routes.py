import os
import logging
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import SkinRecord, Baby
from models import RashType

logger = logging.getLogger(__name__)
scans_bp = Blueprint("scans_bp", __name__, url_prefix="/api/scans")


@scans_bp.before_app_request
def ensure_upload_dir():
    if hasattr(current_app, "uploads_path"):
        os.makedirs(current_app.uploads_path, exist_ok=True)


@scans_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_scans():
    # Optional filter by parent_id (will show scans created by that user or scans for that parent's babies)
    parent_id = request.args.get("parent_id")
    try:
        q = SkinRecord.query
        if parent_id:
            # scans created by this user
            q = q.filter((SkinRecord.created_by_id == parent_id) | (SkinRecord.baby.has(parent_id=parent_id)))
        items = q.order_by(SkinRecord.created_at.desc()).all()
        out = []
        for s in items:
            out.append({
                "id": s.id,
                "baby_id": s.baby_id,
                "baby_name": s.baby.name if s.baby else None,
                "rash_type": s.predicted_rash_type,
                "confidence": s.confidence_score,
                "image_url": url_for("file", filename=s.image_path, _external=False) if s.image_path else None,
                "created_at": s.created_at.isoformat()
            })
        return jsonify(out)
    except Exception:
        logger.exception("Failed listing scans")
        return jsonify({"error": "Failed to list scans"}), 500


@scans_bp.route("/<int:scan_id>", methods=["GET"])
@jwt_required(optional=True)
def get_scan(scan_id):
    s = SkinRecord.query.get(scan_id)
    if not s:
        return jsonify({"error": "Not found"}), 404
    # attempt to include care / prevention tips from RashType table
    care_tips = []
    prevention = []
    try:
        rt = RashType.query.filter_by(name=s.predicted_rash_type).first()
        if rt and rt.care_tips:
            import json
            try:
                parsed = json.loads(rt.care_tips)
                if isinstance(parsed, dict):
                    # try to pick english by default
                    def pick(section):
                        val = parsed.get(section, [])
                        if isinstance(val, dict):
                            return val.get('en') or val.get('kn') or []
                        return val
                    care_tips = pick('home_care') or []
                    prevention = pick('prevention') or []
                elif isinstance(parsed, list):
                    care_tips = parsed
            except Exception:
                care_tips = rt.care_tips.splitlines()
    except Exception:
        pass

    return jsonify({
        "id": s.id,
        "baby_id": s.baby_id,
        "baby_name": s.baby.name if s.baby else None,
        "rash_type": s.predicted_rash_type,
        "confidence": s.confidence_score,
        "care_tips": care_tips,
        "prevention_tips": prevention,
        "image_url": url_for("file", filename=s.image_path, _external=False) if s.image_path else None,
        "created_at": s.created_at.isoformat()
    })


@scans_bp.route("", methods=["POST"])
@jwt_required(optional=True)
def create_scan():
    file = request.files.get("file") or request.files.get("image")
    if not file:
        return jsonify({"error": "file field missing"}), 400

    # optional fields
    baby_id = request.form.get("baby_id")
    baby_id = int(baby_id) if baby_id and baby_id.isdigit() else None
    rash_type = request.form.get("rash_type") or request.form.get("label")
    confidence = request.form.get("confidence")
    try:
        confidence = float(confidence) if confidence is not None and confidence != '' else None
    except Exception:
        confidence = None

    # save file
    fname = secure_filename(file.filename or "upload.jpg")
    stem, ext = os.path.splitext(fname)
    ts = __import__("datetime").datetime.utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"{stem}_{ts}{ext or '.jpg'}"
    save_path = os.path.join(current_app.uploads_path, final_name)
    try:
        file.stream.seek(0)
        with open(save_path, "wb") as fh:
            fh.write(file.read())
    except Exception:
        logger.exception("Failed saving uploaded scan file")
        return jsonify({"error": "Failed to save file"}), 500

    user_id = get_jwt_identity()
    try:
        # If baby_id not provided, attempt to associate with the parent's first baby.
        # Some DB schemas require skin_records.baby_id to be non-null; if none exists,
        # create a placeholder baby record named 'Unassigned' for this parent so
        # the FK and NOT NULL constraint are satisfied.
        if baby_id is None:
            try:
                if user_id:
                    first_baby = Baby.query.filter_by(parent_id=user_id).first()
                else:
                    first_baby = Baby.query.first()
                if first_baby:
                    baby_id = first_baby.id
                else:
                    # create a placeholder baby
                    placeholder = Baby(parent_id=user_id, name="Unassigned")
                    db.session.add(placeholder)
                    db.session.commit()
                    baby_id = placeholder.id
            except Exception:
                # fallback: leave baby_id as None (DB may still reject)
                logger.exception('Failed selecting/creating placeholder baby')

        rec = SkinRecord(
            baby_id=baby_id,
            created_by_id=user_id,
            predicted_rash_type=rash_type,
            confidence_score=confidence,
            image_path=final_name
        )
        db.session.add(rec)
        db.session.commit()
    except Exception:
        logger.exception("Failed saving scan record")
        return jsonify({"error": "DB save failed"}), 500

    return jsonify({
        "id": rec.id,
        "baby_id": rec.baby_id,
        "rash_type": rec.predicted_rash_type,
        "confidence": rec.confidence_score,
        "image_url": url_for("file", filename=rec.image_path, _external=False),
        "created_at": rec.created_at.isoformat()
    }), 201
