import jwt
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = 'your_secret_key'

# Role-based Access Control (RBAC)
roles_permissions = {
    'admin': ['create', 'edit', 'delete', 'view'],
    'editor': ['create', 'edit', 'view'],
    'viewer': ['view']
}

# Dummy database for sessions
active_sessions = {}

# Generate JWT Token
def generate_token(username, role):
    token = jwt.encode({'user': username, 'role': role}, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

# Decorator for role-based access control
def requires_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'message': 'Token is missing!'}), 403
            try:
                data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                if data['role'] not in roles_permissions or 'view' not in roles_permissions[data['role']]:
                    return jsonify({'message': 'Access denied!'}), 403
            except Exception:
                return jsonify({'message': 'Token is invalid!'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# API Endpoints
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    role = request.json.get('role')
    token = generate_token(username, role)
    active_sessions[username] = token  # Track active sessions
    return jsonify({'token': token})

@app.route('/protected', methods=['GET'])
@requires_role('viewer')
def protected():
    return jsonify({'message': 'This is a protected route'})

if __name__ == '__main__':
    app.run(debug=True)