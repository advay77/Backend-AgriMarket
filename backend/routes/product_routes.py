from flask import Blueprint, request, jsonify
from extensions import mongo
from jose import jwt as jose_jwt
import os
from bson import ObjectId
from datetime import datetime

bp = Blueprint('products', __name__)

# Rest of your product_routes.py code remains the same

def get_user_id_from_token(token):
    try:
        payload = jose_jwt.decode(token, os.getenv('SECRET_KEY', 'your-secret-key'))
        return payload['user_id']
    except:
        return None

@bp.route('/products', methods=['GET'])
def get_products():
    products = list(mongo.db.products.find())
    return jsonify([{
        'id': str(p['_id']),
        'name': p['name'],
        'description': p['description'],
        'price': p['price'],
        'quantity': p['quantity'],
        'category': p['category'],
        'image_url': p['image_url'],
        'farmer_id': p['farmer_id']
    } for p in products])

@bp.route('/products', methods=['POST'])
def create_product():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    product = {
        'name': data['name'],
        'description': data['description'],
        'price': data['price'],
        'quantity': data['quantity'],
        'category': data.get('category'),
        'image_url': data.get('image_url'),
        'farmer_id': user_id,
        'created_at': datetime.utcnow()
    }
    
    result = mongo.db.products.insert_one(product)
    product['id'] = str(result.inserted_id)
    del product['_id']
    
    return jsonify(product), 201

@bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product['farmer_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    update_data = {k: v for k, v in data.items() if k in ['name', 'description', 'price', 'quantity', 'category', 'image_url']}
    
    mongo.db.products.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': update_data}
    )
    
    return jsonify({'message': 'Product updated successfully'})

@bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product['farmer_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    mongo.db.products.delete_one({'_id': ObjectId(product_id)})
    return jsonify({'message': 'Product deleted successfully'}) 