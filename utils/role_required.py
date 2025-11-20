from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                # role stored as top-level additional_claims (create_access_token(..., additional_claims={"role": ...}))
                user_role = claims.get("role")
                if user_role != required_role:
                    return jsonify({"error": "Unauthorized: Access denied"}), 403
            except Exception:
                return jsonify({"error": "Invalid or missing token"}), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator