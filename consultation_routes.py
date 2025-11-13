from flask import Blueprint, jsonify, request

# Blueprint setup
consult_bp = Blueprint('consult_bp', __name__, url_prefix='/api/consultations')

# Example route for testing
@consult_bp.route('/', methods=['GET'])
def get_consultations():
    return jsonify({"message": "Consultation routes working!"}), 200

# Example POST route (optional, for your Smart Baby Skin Scanner)
@consult_bp.route('/', methods=['POST'])
def create_consultation():
    data = request.get_json()
    return jsonify({
        "message": "Consultation created successfully",
        "data_received": data
    }), 201
