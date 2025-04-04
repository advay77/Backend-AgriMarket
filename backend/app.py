from flask import jsonify
from dotenv import load_dotenv
import os
from extensions import app, mongo

# Load environment variables
load_dotenv()

# MongoDB configuration
app.config["MONGO_URI"] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/agrimarket')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize MongoDB with app
mongo.init_app(app)

# Import routes
from routes import auth_routes, product_routes, order_routes

# Register blueprints
app.register_blueprint(auth_routes.bp)
app.register_blueprint(product_routes.bp)
app.register_blueprint(order_routes.bp)

@app.route('/')
def index():
    return jsonify({"message": "Welcome to AgriMarket API"})

@app.route('/test-db')
def test_db():
    users = list(mongo.db.users.find())
    products = list(mongo.db.products.find())
    orders = list(mongo.db.orders.find())
    
    return jsonify({
        'users': [{'id': str(u['_id']), 'username': u['username'], 'email': u['email']} for u in users],
        'products': [{'id': str(p['_id']), 'name': p['name'], 'price': p['price']} for p in products],
        'orders': [{'id': str(o['_id']), 'total_amount': o['total_amount'], 'status': o['status']} for o in orders]
    })

if __name__ == '__main__':
    app.run(debug=True)