from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from jose import jwt as jose_jwt
from datetime import datetime, timedelta
from extensions import mongo
import os
from bson import ObjectId

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if email exists
    if mongo.db.users.find_one({'email': data['email']}):
        return jsonify({'error': 'Email already exists'}), 400
    
    # Check if username exists
    if mongo.db.users.find_one({'username': data['username']}):
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new user
    user = {
        'username': data['username'],
        'email': data['email'],
        'password_hash': generate_password_hash(data['password']),
        'is_farmer': data.get('is_farmer', False),
        'created_at': datetime.utcnow()
    }
    
    result = mongo.db.users.insert_one(user)
    
    return jsonify({
        'message': 'User created successfully',
        'user_id': str(result.inserted_id)
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({'email': data['email']})
    
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = jose_jwt.encode({
        'user_id': str(user['_id']),
        'exp': datetime.utcnow() + timedelta(days=1)
    }, os.getenv('SECRET_KEY', 'your-secret-key'))
    
    return jsonify({
        'token': token,
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'is_farmer': user['is_farmer']
        }
    }) 