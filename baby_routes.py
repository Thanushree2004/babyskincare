from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Baby
from sqlalchemy.exc import SQLAlchemyError

baby_bp = Blueprint('baby_bp', __name__, url_prefix='/api/babies')


# -----------------------------------------------------------
#  ADD BABY
# -----------------------------------------------------------
@baby_bp.route('/add', methods=['POST'])
@jwt_required()
def add_baby():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        name = data.get("name")
        dob = data.get("date_of_birth")

        if not name or not dob:
            return jsonify({"error": "name and date_of_birth are required"}), 400

        baby = Baby(
            parent_id=user_id,
            name=name,
            date_of_birth=dob
        )

        db.session.add(baby)
        db.session.commit()

        return jsonify({"message": "Baby added successfully!"}), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# -----------------------------------------------------------
#  GET ALL BABIES OF LOGGED-IN PARENT
# -----------------------------------------------------------
@baby_bp.route('/', methods=['GET'])
@jwt_required()
def get_babies():
    user_id = get_jwt_identity()

    babies = Baby.query.filter_by(parent_id=user_id).all()

    result = [
        {
            "id": b.id,
            "name": b.name,
            "date_of_birth": str(b.date_of_birth),
            "created_at": str(b.created_at)
        }
        for b in babies
    ]

    return jsonify(result), 200



# -----------------------------------------------------------
#  GET SINGLE BABY DETAILS
# -----------------------------------------------------------
@baby_bp.route('/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_baby(baby_id):
    user_id = get_jwt_identity()

    baby = Baby.query.filter_by(id=baby_id, parent_id=user_id).first()

    if not baby:
        return jsonify({"error": "Baby not found"}), 404

    return jsonify({
        "id": baby.id,
        "name": baby.name,
        "date_of_birth": str(baby.date_of_birth),
        "created_at": str(baby.created_at)
    }), 200



# -----------------------------------------------------------
#  UPDATE BABY DETAILS
# -----------------------------------------------------------
@baby_bp.route('/<int:baby_id>/update', methods=['PUT'])
@jwt_required()
def update_baby(baby_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    baby = Baby.query.filter_by(id=baby_id, parent_id=user_id).first()

    if not baby:
        return jsonify({"error": "Baby not found"}), 404

    baby.name = data.get("name", baby.name)
    baby.date_of_birth = data.get("date_of_birth", baby.date_of_birth)

    db.session.commit()

    return jsonify({"message": "Baby updated successfully"}), 200



# -----------------------------------------------------------
#  DELETE BABY
# -----------------------------------------------------------
@baby_bp.route('/<int:baby_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_baby(baby_id):
    user_id = get_jwt_identity()

    baby = Baby.query.filter_by(id=baby_id, parent_id=user_id).first()

    if not baby:
        return jsonify({"error": "Baby not found"}), 404

    db.session.delete(baby)
    db.session.commit()

    return jsonify({"message": "Baby deleted successfully"}), 200
