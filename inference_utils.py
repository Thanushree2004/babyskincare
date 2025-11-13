import os
import io
import json
import numpy as np
from PIL import Image
import tensorflow as tf

ROOT = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ROOT, "unified_model.keras")
LABELS_PATH = os.path.join(ROOT, "class_index_to_label.json")

# load labels (index -> label)
def _load_labels(path=LABELS_PATH):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if all(str(k).isdigit() for k in d.keys()):
            mapping = {int(k): v for k, v in d.items()}
            return [mapping[i] for i in sorted(mapping.keys())]
        # if it's label->index, invert
        inv = {int(v): k for k, v in d.items()}
        return [inv[i] for i in sorted(inv.keys())]
    except Exception:
        return []

CLASS_NAMES = _load_labels()

_model = None
_input_size = (224, 224)

def load_model(path=None):
    global _model, _input_size
    if _model is not None:
        return _model
    p = path or MODEL_PATH
    if not os.path.exists(p):
        raise FileNotFoundError(f"Model not found at {p}")
    _model = tf.keras.models.load_model(p)
    try:
        ishape = _model.input_shape
        if ishape and len(ishape) == 4:
            _, h, w, _ = ishape
            _input_size = (int(h) or 224, int(w) or 224)
    except Exception:
        _input_size = (224, 224)
    return _model

def _open_image(obj, size=None):
    # accept bytes, file-like (Flask FileStorage), or path
    if hasattr(obj, "read"):
        obj.seek(0)
        data = obj.read()
        bio = io.BytesIO(data)
        img = Image.open(bio)
    elif isinstance(obj, (bytes, bytearray)):
        img = Image.open(io.BytesIO(obj))
    else:
        img = Image.open(obj)
    img = img.convert("RGB")
    if size:
        img = img.resize(size, Image.BICUBIC)
    return img

def predict_image_bytes(fileobj):
    """
    Accepts a Flask FileStorage or bytes or path.
    Returns a JSON-serializable dict:
      { rash_type, confidence, confidence_raw, care_tips, probs }
    """
    model = load_model()
    img = _open_image(fileobj, size=_input_size)
    arr = np.asarray(img).astype(np.float32)
    arr = tf.keras.applications.efficientnet.preprocess_input(arr)  # same as training
    inp = np.expand_dims(arr, 0)  # (1,H,W,3)
    preds = model.predict(inp)
    # handle dict or array outputs
    if isinstance(preds, dict):
        # take first item
        preds = list(preds.values())[0]
    preds = np.asarray(preds)
    if preds.ndim == 2 and preds.shape[0] == 1:
        probs = preds[0]
    elif preds.ndim == 1:
        probs = preds
    else:
        # fallback: flatten
        probs = preds.flatten()

    # If outputs not normalized, apply softmax
    if not (probs.min() >= 0 and np.isclose(probs.sum(), 1.0, atol=1e-2)):
        e = np.exp(probs - np.max(probs))
        probs = e / e.sum()

    top_idx = int(np.argmax(probs))
    top_score = float(probs[top_idx])
    top_label = CLASS_NAMES[top_idx] if CLASS_NAMES and top_idx < len(CLASS_NAMES) else f"label_{top_idx}"

    probs_map = {}
    for i, p in enumerate(probs.tolist()):
        lbl = CLASS_NAMES[i] if CLASS_NAMES and i < len(CLASS_NAMES) else f"label_{i}"
        probs_map[lbl] = f"{p*100:.2f}%"

    return {
        "rash_type": top_label,
        "confidence": f"{top_score*100:.1f}%",
        "confidence_raw": float(top_score),
        "care_tips": [],   # app.py / frontend will map label -> tips
        "probs": probs_map
    }