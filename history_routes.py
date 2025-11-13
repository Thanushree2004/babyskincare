from flask import Blueprint, jsonify, request

# Define blueprint
history_bp = Blueprint('history_bp', __name__, url_prefix='/api/history')

# Example GET route — retrieve history records
@history_bp.route('/', methods=['GET'])
def get_history():
    return jsonify({"message": "History routes working!"}), 200

# Example POST route — just for testing data flow
@history_bp.route('/', methods=['POST'])
def create_history_entry():
    data = request.get_json()
    return jsonify({
        "message": "History entry created successfully!",
        "received_data": data
    }), 201
