from flask import Blueprint, request, jsonify
from extensions import mongo
from jose import jwt as jose_jwt
import os
from bson import ObjectId
from datetime import datetime

bp = Blueprint('orders', __name__)

# Rest of your order_routes.py code remains the same

def get_user_id_from_token(token):
    try:
        payload = jose_jwt.decode(token, os.getenv('SECRET_KEY', 'your-secret-key'))
        return payload['user_id']
    except:
        return None

@bp.route('/orders', methods=['GET'])
def get_orders():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    orders = list(mongo.db.orders.find({'customer_id': user_id}))
    return jsonify([{
        'id': str(order['_id']),
        'total_amount': order['total_amount'],
        'status': order['status'],
        'created_at': order['created_at'].isoformat(),
        'items': [{
            'id': str(item['_id']),
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'price': item['price']
        } for item in order['items']]
    } for order in orders])

@bp.route('/orders', methods=['POST'])
def create_order():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'error': 'No items in order'}), 400
    
    total_amount = 0
    order_items = []
    
    for item in items:
        product = mongo.db.products.find_one({'_id': ObjectId(item['product_id'])})
        if not product:
            return jsonify({'error': f'Product {item["product_id"]} not found'}), 404
        
        if product['quantity'] < item['quantity']:
            return jsonify({'error': f'Not enough quantity for product {product["name"]}'}), 400
        
        order_item = {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'price': product['price']
        }
        
        total_amount += product['price'] * item['quantity']
        order_items.append(order_item)
        
        # Update product quantity
        mongo.db.products.update_one(
            {'_id': ObjectId(item['product_id'])},
            {'$inc': {'quantity': -item['quantity']}}
        )
    
    order = {
        'customer_id': user_id,
        'total_amount': total_amount,
        'status': 'pending',
        'created_at': datetime.utcnow(),
        'items': order_items
    }
    
    result = mongo.db.orders.insert_one(order)
    order['id'] = str(result.inserted_id)
    del order['_id']
    
    return jsonify(order), 201

@bp.route('/orders/<order_id>', methods=['PUT'])
def update_order_status(order_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if order['customer_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    mongo.db.orders.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {'status': data.get('status', order['status'])}}
    )
    
    return jsonify({'message': 'Order status updated successfully'}) 