"""
app.py — FINAL FIXED VERSION
Compatible with your models.py (Conversation + Message included)
No jwt_optional anywhere
No import errors
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os, json, logging

# load .env early
load_dotenv()

# Globals
model = None
CLASS_NAMES = ["class_0", "class_1", "class_2"]

# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Instance & uploads folders
    base_dir = os.path.dirname(__file__)
    instance_path = os.path.join(base_dir, "instance")
    uploads_path = os.path.join(instance_path, "uploads")
    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(uploads_path, exist_ok=True)

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(instance_path, 'babyskincare.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

    # Mail config
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') in ('True', 'true', '1')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    CORS(app)

    # Init extensions
    from extensions import db, migrate, jwt, mail
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # Correct import of ALL models (matches your models.py)
    try:
        from models import (
            User, Baby, RashType, SkinRecord,
            DoctorShare, Comment, Consultation,
            AccessLog, Notification,
            Conversation, Message
        )
    except Exception:
        logging.getLogger(__name__).warning(
            "Model import failed during app startup.",
            exc_info=True
        )

    # Helper for blueprint registration
    def try_register(module_path, bp_name):
        try:
            module = __import__(module_path, fromlist=[bp_name])
            bp = getattr(module, bp_name)
            app.register_blueprint(bp)
            logging.getLogger(__name__).info("Registered: %s.%s", module_path, bp_name)
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Could not import {module_path}.{bp_name}: {e}",
                exc_info=True
            )

    # Blueprints list
    blueprints = [
        ("auth_routes", "auth_bp"),
        ("baby_routes", "baby_bp"),
        ("predict_routes", "predict_bp"),
        ("consultation_routes", "consult_bp"),
        ("history_routes", "history_bp"),
        ("chat_routes", "chat_bp")
    ]

    for mod, bp in blueprints:
        try_register(mod, bp)

    # Health check
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "model_loaded": model is not None,
            "num_labels": len(CLASS_NAMES)
        })

    # Serve uploads
    @app.route("/instance/uploads/<path:filename>")
    def uploaded_file(filename):
        uploads_dir = os.path.join(os.path.dirname(__file__), "instance", "uploads")
        return send_from_directory(uploads_dir, filename, as_attachment=False)

    return app


# ---------------------------------------------------------------------------
# Dev Server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tensorflow as tf
    from inference_utils import predict_image_bytes

    def load_label_map(path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if all(k.isdigit() for k in d.keys()):
                    mapping = {int(k): v for k, v in d.items()}
                else:
                    mapping = {int(v): k for k, v in d.items()}
                max_idx = max(mapping.keys())
                return [mapping.get(i, f"label_{i}") for i in range(max_idx + 1)]
            except Exception:
                logging.getLogger(__name__).warning("Failed to parse label map.", exc_info=True)
        return ["class_0", "class_1", "class_2"]

    BASE_DIR = os.path.dirname(__file__)
    MODEL_PATH = os.path.join(BASE_DIR, "unified_model.keras")
    LABELS_JSON = os.path.join(BASE_DIR, "class_index_to_label.json")

    app = create_app()
    CLASS_NAMES = load_label_map(LABELS_JSON)

    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print("✅ Model loaded successfully")
    except Exception as e:
        model = None
        print("⚠️ Model failed to load:", e)

    with app.app_context():
        from extensions import db
        db.create_all()

    print("🚀 Smart Baby Skin Scanner Backend Running...")
    app.run(host="0.0.0.0", port=5000, debug=True)
