import os
import io
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import SkinRecord, RashType, Baby
from inference_utils import predict_image_bytes, load_model

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict_bp", __name__, url_prefix="/predict")

@predict_bp.before_app_request
def ensure_upload_dir():
    if hasattr(current_app, "uploads_path"):
        os.makedirs(current_app.uploads_path, exist_ok=True)


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


@predict_bp.route("", methods=["POST"])
@jwt_required(optional=True)
def predict():
    file = request.files.get("file") or request.files.get("image")
    if not file:
        return jsonify({"error": "file field missing"}), 400

    # baby_id optional now
    baby_id_raw = request.form.get("baby_id")
    baby_id = _safe_int(baby_id_raw) if baby_id_raw else None
    baby = None
    if baby_id is not None:
        baby = Baby.query.get(baby_id)
        if not baby:
            logger.warning("Baby id %s not found; proceeding without DB record", baby_id)
            baby_id = None

    # Run prediction (EfficientNet preprocessing handled in helper)
    try:
        result = predict_image_bytes(file)
        label = result.get("rash_type", "unknown")
        confidence_raw = result.get("confidence_raw", 0.0)
        confidence_pct = round(confidence_raw * 100.0, 2)
    except FileNotFoundError:
        return jsonify({"error": "Model file missing on server"}), 500
    except Exception as e:
        logger.exception("Inference failed")
        return jsonify({"error": "Inference failed", "detail": str(e)}), 500

    # Care tips from DB if available (structured: home_care, prevention, doctor_if with optional language keys)
    lang = request.args.get("lang", "en").lower()
    care_tips = []
    prevention = []
    doctor_if = []
    try:
        rt = RashType.query.filter_by(name=label).first()
        if rt and rt.care_tips:
            try:
                parsed = json.loads(rt.care_tips)
                if isinstance(parsed, dict):
                    def pick(section):
                        val = parsed.get(section, [])
                        if isinstance(val, dict):
                            # multilingual structure { 'en': [...], 'kn': [...] }
                            return val.get(lang) or val.get("en") or []
                        return val
                    care_tips = pick("home_care")
                    prevention = pick("prevention")
                    doctor_if = pick("doctor_if")
                elif isinstance(parsed, list):
                    care_tips = parsed
            except Exception:
                care_tips = rt.care_tips.splitlines()
    except Exception:
        logger.warning("Care tips lookup failed", exc_info=True)

    logger.info("PREDICTION label=%s confidence=%.2f%% baby_id=%s", label, confidence_pct, baby_id)

    return jsonify({
        "rash_type": label,
        "confidence": confidence_pct,
        "care_tips": care_tips,
        "prevention_tips": prevention,
        "consult_doctor_if": doctor_if,
        "probs": result.get("probs", {})
    }), 200