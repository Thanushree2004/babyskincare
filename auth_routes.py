from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


# ==================================
# LOGIN (Parent / Doctor)
# ==================================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create JWT token: use string subject and keep role in additional_claims
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "user_id": user.id,
        "role": user.role,
        "full_name": user.full_name
    }), 200