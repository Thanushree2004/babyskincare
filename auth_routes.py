from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from extensions import db
from models import User

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    # Validate presence of fields
    if not full_name or not email or not password or not role:
        return jsonify({"error": "All fields required"}), 400

    # Normalize role to match DB format
    role = role.capitalize()  # "parent" → "Parent", "doctor" → "Doctor"

    if role not in ["Parent", "Doctor"]:
        return jsonify({"error": "Invalid role"}), 400

    # Check if email already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    # Hash password
    hashed = generate_password_hash(password)

    # Create user object
    user = User(
        full_name=full_name,
        email=email,
        password_hash=hashed,
        role=role
    )

    # Save to DB
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Account created successfully!",
        "role": role,
        "full_name": full_name
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Create JWT (can include role for quick access)
    additional_claims = {"role": user.role.lower()}
    # Some PyJWT versions require the 'sub' (identity) to be a string.
    # Ensure identity is serialized as a string to avoid "Subject must be a string" errors.
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "full_name": user.full_name,
        "role": user.role.lower()
    })
