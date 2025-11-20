from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Conversation, Message

chat_bp = Blueprint("chat_bp", __name__, url_prefix="/api/chat")

# 1) Create or get conversation (parent creates with doctor)
@chat_bp.route("/conversations", methods=["POST"])
@jwt_required()
def create_conversation():
    data = request.get_json() or {}
    user_id = get_jwt_identity()
    doctor_id = data.get("doctor_id")
    # ensure doctor exists
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # If current user is doctor, treat other id as parent
    current = User.query.get(user_id)
    if current.role == "doctor":
        parent_id = data.get("parent_id")
        if not parent_id:
            return jsonify({"error": "parent_id required for doctors"}), 400
    else:
        parent_id = user_id

    # find existing conversation
    conv = Conversation.query.filter_by(parent_id=parent_id, doctor_id=doctor_id).first()
    if conv:
        return jsonify({"conversation_id": conv.id}), 200

    conv = Conversation(parent_id=parent_id, doctor_id=doctor_id)
    db.session.add(conv)
    db.session.commit()
    return jsonify({"conversation_id": conv.id}), 201


# 2) List conversations for current user
@chat_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user.role == "doctor":
        convs = Conversation.query.filter_by(doctor_id=user_id).order_by(Conversation.created_at.desc()).all()
    else:
        convs = Conversation.query.filter_by(parent_id=user_id).order_by(Conversation.created_at.desc()).all()

    out = []
    for c in convs:
        other = User.query.get(c.doctor_id) if user.role == "parent" else User.query.get(c.parent_id)
        last_msg = Message.query.filter_by(conversation_id=c.id).order_by(Message.created_at.desc()).first()
        out.append({
            "conversation_id": c.id,
            "other_id": other.id,
            "other_name": other.full_name,
            "last_message": last_msg.text if last_msg else None,
            "last_at": last_msg.created_at.strftime("%Y-%m-%d %H:%M") if last_msg else None
        })
    return jsonify({"conversations": out}), 200


# 3) Get messages for a conversation (paged simple)
@chat_bp.route("/conversations/<int:conv_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(conv_id):
    user_id = get_jwt_identity()
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    # Check user is participant
    if user_id not in (conv.parent_id, conv.doctor_id):
        return jsonify({"error": "Access denied"}), 403

    # optional pagination
    limit = int(request.args.get("limit", 100))
    messages = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.asc()).limit(limit).all()

    out = [{
        "id": m.id,
        "sender_id": m.sender_id,
        "text": m.text,
        "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "read": m.read
    } for m in messages]

    return jsonify({"conversation_id": conv_id, "messages": out}), 200


# 4) Send message to a conversation
@chat_bp.route("/conversations/<int:conv_id>/messages", methods=["POST"])
@jwt_required()
def send_message(conv_id):
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400

    user_id = get_jwt_identity()
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    if user_id not in (conv.parent_id, conv.doctor_id):
        return jsonify({"error": "Access denied"}), 403

    msg = Message(conversation_id=conv_id, sender_id=user_id, text=text)
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "message_id": msg.id,
        "conversation_id": conv_id,
        "text": msg.text,
        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }), 201


# 5) Mark messages as read (mark all in conv as read by recipient)
@chat_bp.route("/conversations/<int:conv_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(conv_id):
    user_id = get_jwt_identity()
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    if user_id not in (conv.parent_id, conv.doctor_id):
        return jsonify({"error": "Access denied"}), 403

    # Mark messages not sent by current user as read
    Message.query.filter(Message.conversation_id == conv_id, Message.sender_id != user_id, Message.read == False).update({"read": True})
    db.session.commit()
    return jsonify({"message": "marked read"}), 200
