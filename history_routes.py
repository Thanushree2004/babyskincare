from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import SkinRecord, Baby

history_bp = Blueprint("history_bp", __name__, url_prefix="/api/history")


# ---------------------------------------------------------
# 1️⃣ GET: Fetch history for ONE baby
# ---------------------------------------------------------
@history_bp.route("/<int:baby_id>", methods=["GET"])
@jwt_required()
def get_history(baby_id):
    user_id = get_jwt_identity()

    # Check ownership
    baby = Baby.query.filter_by(id=baby_id, parent_id=user_id).first()
    if not baby:
        return jsonify({"error": "Baby not found or unauthorized"}), 404

    records = (
        SkinRecord.query
        .filter_by(baby_id=baby_id)
        .order_by(SkinRecord.created_at.desc())
        .all()
    )

    history_list = [
        {
            "record_id": rec.id,
            "rash_type": rec.predicted_rash_type,
            "confidence": rec.confidence_score,
            "image_url": rec.image_path,
            "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for rec in records
    ]

    return jsonify({
        "baby_id": baby.id,
        "baby_name": baby.name,
        "total_records": len(history_list),
        "history": history_list,
    }), 200


# ---------------------------------------------------------
# 2️⃣ GET: Fetch history for ALL babies of the parent
# ---------------------------------------------------------
@history_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_history():
    user_id = get_jwt_identity()

    babies = Baby.query.filter_by(parent_id=user_id).all()

    history_output = []

    for baby in babies:
        records = (
            SkinRecord.query
            .filter_by(baby_id=baby.id)
            .order_by(SkinRecord.created_at.desc())
            .all()
        )

        record_list = [
            {
                "record_id": rec.id,
                "rash_type": rec.predicted_rash_type,
                "confidence": rec.confidence_score,
                "image_url": rec.image_path,
                "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for rec in records
        ]

        history_output.append({
            "baby_id": baby.id,
            "baby_name": baby.name,
            "total_records": len(record_list),
            "records": record_list,
        })

    return jsonify({"history": history_output}), 200
