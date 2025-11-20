import os
import logging
from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLASS_NAMES = ["class_0", "class_1", "class_2"]


# -------------------------------------------------------------
# APPLICATION FACTORY
# -------------------------------------------------------------
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ------------------ FOLDERS ------------------
    base_dir = os.path.dirname(__file__)
    instance_path = os.path.join(base_dir, "instance")
    uploads_path = os.path.join(instance_path, "uploads")

    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(uploads_path, exist_ok=True)

    # ------------------ DATABASE ------------------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(instance_path, 'babyskincare.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ------------------ SECRETS ------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")

    # ------------------ MAIL ------------------
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") in ("True", "true", "1")
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    # ------------------ CORS ------------------
    from flask_cors import CORS
    CORS(app, resources={r"/*": {"origins": [
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "*"
    ]}}, supports_credentials=True)

    # ------------------ EXTENSIONS ------------------
    from extensions import db, migrate, jwt, mail
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # Store paths
    app.instance_path_dir = instance_path
    app.uploads_path = uploads_path
    app.model = None
    app.class_names = CLASS_NAMES

    # ------------------ MODELS SAFE IMPORT ------------------
    try:
        import models
        logger.info("Models loaded successfully.")
    except Exception:
        logger.warning("Model import failed — continuing.", exc_info=True)

    # ------------------ BLUEPRINT LOADER ------------------
    def register(bp_file, bp_name):
        try:
            module = __import__(bp_file, fromlist=[bp_name])
            bp = getattr(module, bp_name)
            app.register_blueprint(bp)
            logger.info(f"Registered {bp_file}.{bp_name}")
        except Exception as e:
            logger.warning(f"Skipping {bp_file} → {e}")

    blueprints = [
        ("auth_routes", "auth_bp"),
        ("baby_routes", "baby_bp"),
        ("predict_routes", "predict_bp"),
        ("parent_routes", "parent_bp"),
        ("consultation_routes", "consult_bp"),
        ("history_routes", "history_bp"),
        ("chat_routes", "chat_bp"),
    ]

    for file, bp in blueprints:
        register(file, bp)

    # ------------------ ROUTES ------------------
    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "model_loaded": app.model is not None,
            "labels": app.class_names
        })

    @app.route("/instance/uploads/<path:filename>")
    def file(filename):
        return send_from_directory(app.uploads_path, filename)

    @app.route("/", defaults={"path": "login.html"})
    @app.route("/<path:path>")
    def serve_frontend(path):
        template_path = os.path.join("templates", path)
        if os.path.exists(template_path):
            return send_from_directory("templates", path)
        return send_from_directory("templates", "login.html")

    @app.errorhandler(404)
    def nf(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def se(e):
        logger.error("Server error", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app

# -------------------------------------------------------------
# RUN FLASK SERVER
# -------------------------------------------------------------
if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, port=5500)
