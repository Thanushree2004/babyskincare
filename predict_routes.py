import os
import io
import json
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import SkinRecord, RashType, Baby

import numpy as np
from keras.models import load_model


predict_bp = Blueprint("predict_bp", __name__, url_prefix="/predict")

MODEL = None
CLASS_MAP = None
IMG_SIZE = (224, 224)

# Correct uploads folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "instance", "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Correct model path (use same as app.py)
MODEL_PATH = os.path.join(os.path.dirname(BASE_DIR), "unified_model.keras")


# --------------------------------------------------
# Load model + labels once
# --------------------------------------------------
def load_model_and_labels():
    global MODEL, CLASS_MAP

    if MODEL is None:
        print("📌 Loading model from:", MODEL_PATH)
        MODEL = load_model(MODEL_PATH)
        print("✅ Model loaded successfully")

    if CLASS_MAP is None:
        labels_file = os.path.join(os.path.dirname(BASE_DIR), "class_index_to_label.json")

        if os.path.exists(labels_file):
            with open(labels_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            CLASS_MAP = {int(k): v for k, v in data.items()}
        else:
            CLASS_MAP = {0: "class_0", 1: "class_1", 2: "class_2"}

        print("✅ Labels loaded:", CLASS_MAP)

    return MODEL, CLASS_MAP


# --------------------------------------------------
# Preprocess image
# --------------------------------------------------
def preprocess_image(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE)

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

    # Validate baby exists
    baby = Baby.query.get(baby_id)
    if not baby:
        return jsonify({"error": "Invalid baby ID"}), 400

    # Load model + labels
    model, class_map = load_model_and_labels()

    img_bytes = file.read()

    # -------------------- Predict --------------------
    try:
        x = preprocess_image(img_bytes)
        preds = model.predict(x)[0]

        top_idx = int(np.argmax(preds))
        confidence = float(preds[top_idx]) * 100
        label = class_map.get(top_idx, f"class_{top_idx}")

    except Exception as e:
        print("❌ Prediction error:", e)
        return jsonify({"error": "Model prediction failed"}), 500

    # ---------------- File Save ----------------------
    fname = secure_filename(file.filename)
    base, ext = os.path.splitext(fname)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    final_name = f"{base}_{timestamp}{ext}"

    save_path = os.path.join(UPLOAD_DIR, final_name)
    with open(save_path, "wb") as f:
        f.write(img_bytes)

    image_url = f"/instance/uploads/{final_name}"

    # --------------- Care Tips From DB ---------------
    care_tips = ["If uncertain, consult a pediatrician"]

    row = RashType.query.filter_by(name=label).first()
    if row and row.care_tips:
        try:
            parsed = json.loads(row.care_tips)
            care_tips = parsed if isinstance(parsed, list) else [row.care_tips]
        except:
            care_tips = row.care_tips.split("\n")

    # --------------- Save record in DB ---------------
    user_id = get_jwt_identity()

    record = SkinRecord(
        baby_id=baby_id,
        created_by_id=user_id,
        predicted_rash_type=label,
        confidence_score=confidence,
        image_path=image_url
    )

    db.session.add(record)
    db.session.commit()

    # ---------------- Final Response -----------------
    return jsonify({
        "rash_type": label,
        "confidence": round(confidence, 2),
        "care_tips": care_tips,
        "record_id": record.id,
        "image_url": image_url
    }), 200
