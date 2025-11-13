from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os, json

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///babyskincare.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# ------------------------------------------------------------
# INITIALIZE EXTENSIONS
# ------------------------------------------------------------
from extensions import db, migrate, jwt, mail

db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
mail.init_app(app)

# ------------------------------------------------------------
# IMPORT MODELS (AFTER db.init_app TO AVOID CIRCULAR IMPORT)
# ------------------------------------------------------------
from models import User, Baby, RashType, SkinRecord, DoctorShare, Comment, Consultation

# ------------------------------------------------------------
# REGISTER BLUEPRINTS
# ------------------------------------------------------------
from auth_routes import auth_bp
from baby_routes import baby_bp
from predict_routes import predict_bp
from consultation_routes import consult_bp
from history_routes import history_bp

app.register_blueprint(auth_bp)
app.register_blueprint(baby_bp)
app.register_blueprint(predict_bp)
app.register_blueprint(consult_bp)
app.register_blueprint(history_bp)

# ------------------------------------------------------------
# HEALTH CHECK ROUTE
# ------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None,
        "num_labels": len(CLASS_NAMES)
    })

# ------------------------------------------------------------
# ML MODEL SETUP
# ------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "unified_model.keras")
LABELS_JSON = os.path.join(os.path.dirname(__file__), "class_index_to_label.json")
model = None
CLASS_NAMES = ["class_0", "class_1", "class_2"]

# ------------------------------------------------------------
# DEVELOPMENT SERVER ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    import tensorflow as tf
    from inference_utils import predict_image_bytes

    def load_label_map(path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if all(isinstance(k, str) and k.isdigit() for k in d.keys()):
                    mapping = {int(k): v for k, v in d.items()}
                else:
                    mapping = {int(v): k for k, v in d.items()}
                max_idx = max(mapping.keys())
                return [mapping.get(i, f"label_{i}") for i in range(max_idx + 1)]
            except Exception as e:
                print("⚠️ Failed to load label map:", e)
        return ["class_0", "class_1", "class_2"]

    CLASS_NAMES = load_label_map(LABELS_JSON)

    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print("⚠️ Model failed to load:", e)
        model = None

    # Ensure DB tables exist when running locally
    with app.app_context():
        db.create_all()

    print("🚀 Starting Smart Baby Skin Scanner Backend...")
    app.run(host="0.0.0.0", port=5000, debug=True)
