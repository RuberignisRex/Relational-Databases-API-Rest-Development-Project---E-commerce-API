# installing dependencies
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, select
from sqlalchemy.orm import relationship
import os

# initializing flask app
app = Flask(__name__)

# database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:RCHsqlDB@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# creating base model
class Base(DeclarativeBase):
    pass

# initializing SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

# Models
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship(back_populates="orders")
    products: Mapped[list["OrderProduct"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    
class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    orders: Mapped[list["OrderProduct"]] = relationship(back_populates="product", cascade="all, delete-orphan")

# Defining Association table for many-to-many relationship between Orders and Products 
class OrderProduct(Base):
    __tablename__ = 'order_product'
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    order: Mapped[Order] = relationship(back_populates="products")
    product: Mapped[Product] = relationship(back_populates="orders")

# Schemas
# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        
# Order Schema
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True
        
# Product Schema
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        include_fk = True

# initializing schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Creating API endpoints for CRUD operations on Users
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], address=user_data['address'], email=user_data['email'])
    db.session.add(new_user)
    db.session.commit()
    
    return user_schema.jsonify(new_user), 201

@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()
    
    return users_schema.jsonify(users), 200

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return user_schema.jsonify(user), 200

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.address = user_data['address']
    user.email = user_data['email']
    
    db.session.commit()
    
    return user_schema.jsonify(user), 200

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': f'User {id} has been deleted'}), 200

# Creatiing API endpoints for CRUD operations on Pruducts
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(name=product_data['name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    
    return product_schema.jsonify(new_product), 201

@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()
    
    return products_schema.jsonify(products), 200

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    return product_schema.jsonify(product), 200

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']
    
    db.session.commit()
    
    return product_schema.jsonify(product), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': f'Product{id} has been deleted'}), 200

# Creating API endpoints for CRUD operations on Orders and associating them with Users and Products
# using POST to create a new order and associate it with a user. also requires the order date
@app.route('/orders', methods=['POST'])
def create_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user_id = order_data['user_id']
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    new_order = Order(order_date=order_data['order_date'], user_id=user_id)
    db.session.add(new_order)
    db.session.commit()
    
    return order_schema.jsonify(new_order), 201

# adding a product to an order with a specified quantity while preventing duplicate entries in the association table
@app.route('/orders/<int:order_id>/products/<int:product_id>', methods=['POST'])
def add_product_to_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)
    
    if not order or not product:
        return jsonify({'message': 'Order or Product not found'}), 404
    
    existing_entry = db.session.query(OrderProduct).filter_by(order_id=order_id, product_id=product_id).first()
    if existing_entry:
        return jsonify({'message': 'Product already associated with this order'}), 400
    
    quantity = request.json.get('quantity', 1)
    order_product = OrderProduct(order_id=order_id, product_id=product_id, quantity=quantity)
    db.session.add(order_product)
    db.session.commit()
    
    return jsonify({'message': f'Product {product_id} has been added to Order {order_id} with quantity {quantity}'}), 200

# using DELETE to remove a product from an order and ensure that the association is properly removed from the database
@app.route('/orders/<int:order_id>/products/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order_product = db.session.query(OrderProduct).filter_by(order_id=order_id, product_id=product_id).first()
    
    if not order_product:
        return jsonify({'message': 'Product not associated with this order'}), 404
    
    db.session.delete(order_product)
    db.session.commit()
    
    return jsonify({'message': f'Product {product_id} has been removed from Order {order_id}'}), 200

# retrieving all orders associated with a specific user
@app.route('/users/<int:user_id>/orders', methods=['GET'])
def get_orders_for_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    orders = user.orders
    return orders_schema.jsonify(orders), 200

# retrieving all products associated with a specific order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    products = [op.product for op in order.products]
    return products_schema.jsonify(products), 200


# running the app
if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()  # Uncomment this line to drop all existing tables before creating new ones
        db.create_all()
        
    app.run(debug=True)