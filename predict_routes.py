import os
import io
import json
import logging
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import SkinRecord, RashType, Baby

import numpy as np

# prefer tensorflow.keras for compatibility; fallback to keras if needed
try:
    from tensorflow.keras.models import load_model as tf_load_model
except Exception:
    try:
        from keras.models import load_model as tf_load_model
    except Exception:
        tf_load_model = None

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict_bp", __name__, url_prefix="/predict")

MODEL = None
CLASS_MAP = None
IMG_SIZE = (224, 224)

# Correct model path (same as app.py - project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "unified_model.keras")
LABELS_PATH = os.path.join(BASE_DIR, "class_index_to_label.json")


@predict_bp.before_app_request
def ensure_upload_dir():
    # reuse the app's uploads directory
    if hasattr(current_app, "uploads_path"):
        os.makedirs(current_app.uploads_path, exist_ok=True)


# --------------------------------------------------
# Load model + labels once (lazy)
# --------------------------------------------------
def load_model_and_labels():
    global MODEL, CLASS_MAP

    if MODEL is None:
        if tf_load_model is None:
            logger.error("No keras/tensorflow loader available")
            raise RuntimeError("Model loader not available in environment")
        if not os.path.exists(MODEL_PATH):
            logger.warning("Model file not found at %s", MODEL_PATH)
            raise FileNotFoundError("Model file not found")
        try:
            logger.info("Loading model from: %s", MODEL_PATH)
            MODEL = tf_load_model(MODEL_PATH)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.exception("Failed to load model")
            raise

    if CLASS_MAP is None:
        if os.path.exists(LABELS_PATH):
            try:
                with open(LABELS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # data can be {"0": "label"} or {"label": 0}
                # convert to index -> label
                if all(str(k).isdigit() for k in data.keys()):
                    CLASS_MAP = {int(k): v for k, v in data.items()}
                else:
                    # invert mapping label->index to index->label
                    CLASS_MAP = {int(v): k for k, v in data.items()}
            except Exception:
                logger.exception("Failed to parse labels file; using defaults")
                CLASS_MAP = {0: "class_0", 1: "class_1", 2: "class_2"}
        else:
            CLASS_MAP = {0: "class_0", 1: "class_1", 2: "class_2"}

        logger.info("Labels loaded: %s", CLASS_MAP)

    return MODEL, CLASS_MAP


# --------------------------------------------------
# Preprocess image
# --------------------------------------------------
def preprocess_image(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE, Image.BICUBIC)
    arr = np.array(img).astype("float32") / 255.0
    arr = np.expand_dims(arr, axis=0)
    return arr


# --------------------------------------------------
# PREDICT ENDPOINT
# --------------------------------------------------
@predict_bp.route("", methods=["POST"])
@jwt_required(optional=True)
def predict():
    if "file" not in request.files:
        return jsonify({"error": "Image file missing"}), 400

    file = request.files["file"]
    baby_id = request.form.get("baby_id")

    if not baby_id:
        return jsonify({"error": "baby_id is required"}), 400

    # ensure baby_id is integer
    try:
        baby_id_int = int(baby_id)
    except Exception:
        return jsonify({"error": "baby_id must be an integer"}), 400

    # Validate baby exists
    baby = Baby.query.get(baby_id_int)
    if not baby:
        return jsonify({"error": "Invalid baby ID"}), 400

    # Load model + labels (handle missing model)
    try:
        model, class_map = load_model_and_labels()
    except FileNotFoundError:
        return jsonify({"error": "Model file not found on server"}), 500
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.exception("Failed to prepare model/labels")
        return jsonify({"error": "Model loading failed", "detail": str(e)}), 500

    img_bytes = file.read()

    # -------------------- Predict --------------------
    try:
        x = preprocess_image(img_bytes)
        preds = model.predict(x)
        # handle different shapes
        if preds.ndim == 2:
            preds = preds[0]
        top_idx = int(np.argmax(preds))
        confidence = float(preds[top_idx]) * 100.0
        label = class_map.get(top_idx, f"class_{top_idx}")
    except Exception as e:
        logger.exception("Prediction error")
        return jsonify({"error": "Model prediction failed", "detail": str(e)}), 500

    # ---------------- File Save ----------------------
    fname = secure_filename(file.filename or "upload.jpg")
    base, ext = os.path.splitext(fname)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    final_name = f"{base}_{timestamp}{ext or '.jpg'}"

    try:
        with open(final_name, "wb") as f:
            f.write(img_bytes)
    except Exception:
        logger.exception("Failed to save uploaded file")

    # --------------- Care Tips From DB ---------------
    care_tips = ["If uncertain, consult a pediatrician"]
    try:
        row = RashType.query.filter_by(name=label).first()
        if row and row.care_tips:
            try:
                parsed = json.loads(row.care_tips)
                care_tips = parsed if isinstance(parsed, list) else [row.care_tips]
            except Exception:
                care_tips = row.care_tips.splitlines()
    except Exception:
        logger.exception("Failed to fetch care tips")

    # --------------- Save record in DB ---------------
    user_id = get_jwt_identity()  # may be None for anonymous

    try:
        record = SkinRecord(
            baby_id=baby_id_int,
            created_by_id=user_id,
            predicted_rash_type=label,
            confidence_score=round(confidence, 2),
            image_path=final_name
        )

        db.session.add(record)
        db.session.commit()
    except Exception:
        logger.exception("Failed to save prediction record")
        # continue without failing the entire request

    # ---------------- Final Response -----------------
    return jsonify({
        "rash_type": label,
        "confidence": round(confidence, 2),
        "care_tips": care_tips,
        "record_id": getattr(record, "id", None),
        "image_url": final_name
    }), 200