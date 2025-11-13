from flask import Blueprint, request, jsonify

predict_bp = Blueprint('predict_bp', __name__, url_prefix='/api/predict')

@predict_bp.route('/', methods=['POST'])
def predict():
    # simple test endpoint
    return jsonify({"message": "Predict route working"}), 200
