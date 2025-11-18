from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # Ensure JWT exists
                verify_jwt_in_request()

                # Get JWT claims
                claims = get_jwt()

                # Identity is stored under "sub"
                identity = claims.get("sub", {})
                user_role = identity.get("role")

                # Check role
                if user_role != required_role:
                    return jsonify({"error": "Unauthorized: Access denied"}), 403

            except Exception:
                return jsonify({"error": "Invalid or missing token"}), 401

            # Allowed → run function
            return fn(*args, **kwargs)

        return wrapper
    return decorator
