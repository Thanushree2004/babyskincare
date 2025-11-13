from flask import Blueprint, request, jsonify
from datetime import timedelta
from extensions import db
from models import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password required"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400
    user = User(email=data["email"], full_name=data.get("full_name", ""), role=data.get("role", "parent"))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "registered", "user_id": user.id}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=30))
    return jsonify({"access_token": access_token, "user_id": user.id}), 200