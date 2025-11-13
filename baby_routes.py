from flask import Blueprint, jsonify

baby_bp = Blueprint('baby_bp', __name__, url_prefix='/api/babies')

@baby_bp.route('/', methods=['GET'])
def get_babies():
    return jsonify({"message": "Get babies"}), 200
