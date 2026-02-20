from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from config import DevelopmentConfig

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

db = SQLAlchemy(app)


# ==================== Database Models ====================

class Product(db.Model):
    """Product Model"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('OrderItem', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'image_url': self.image_url
        }


class Order(db.Model):
    """Order Model"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    shipping_address = db.Column(db.String(300), nullable=False)
    shipping_city = db.Column(db.String(50), nullable=False)
    shipping_state = db.Column(db.String(50))
    shipping_zip = db.Column(db.String(10))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Processing, Shipped, Delivered, Cancelled
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    """Order Items Model"""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(10))
    color = db.Column(db.String(50))
    price_at_purchase = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product.name,
            'quantity': self.quantity,
            'size': self.size,
            'color': self.color,
            'price_at_purchase': self.price_at_purchase,
            'subtotal': self.quantity * self.price_at_purchase
        }


class Review(db.Model):
    """Product Review Model"""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='reviews')


# ==================== Helper Functions ====================

def generate_order_number():
    """Generate unique order number"""
    import random
    import string
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"ORD-{timestamp}-{random_str}"


def get_cart_from_session():
    """Get cart from session"""
    return session.get('cart', {})


def save_cart_to_session(cart):
    """Save cart to session"""
    session['cart'] = cart
    session.modified = True


# ==================== Routes ====================

@app.route('/')
def index():
    """Home page"""
    featured_products = Product.query.limit(6).all()
    return render_template('index.html', featured_products=featured_products)


@app.route('/shop')
def shop():
    """Shop page with all products"""
    category = request.args.get('category', None)
    sort = request.args.get('sort', 'name')

    query = Product.query

    if category:
        query = query.filter_by(category=category)

    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())

    products = query.all()
    categories = db.session.query(Product.category).distinct().all()

    return render_template('shop.html', products=products, categories=categories, current_category=category)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(product_id=product_id).scalar() or 0

    return render_template('product_detail.html', product=product, reviews=reviews, avg_rating=avg_rating)


@app.route('/cart')
def cart():
    """View shopping cart"""
    cart = get_cart_from_session()

    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * item_data['quantity']
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'size': item_data.get('size'),
                'color': item_data.get('color'),
                'subtotal': item_total
            })
            total_price += item_total

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    size = request.form.get('size', '')
    color = request.form.get('color', '')

    if quantity < 1:
        flash('Invalid quantity', 'error')
        return redirect(request.referrer)

    if product.stock < quantity:
        flash('Insufficient stock', 'error')
        return redirect(request.referrer)

    cart = get_cart_from_session()

    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str]['quantity'] += quantity
    else:
        cart[product_id_str] = {
            'quantity': quantity,
            'size': size,
            'color': color
        }

    save_cart_to_session(cart)
    flash(f'Added {product.name} to cart', 'success')
    return redirect(request.referrer)


@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove product from cart"""
    cart = get_cart_from_session()
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]
        save_cart_to_session(cart)
        flash('Item removed from cart', 'success')

    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    cart = get_cart_from_session()

    if not cart:
        flash('Your cart is empty', 'error')
        return redirect(url_for('shop'))

    if request.method == 'POST':
        try:
            # Create order
            order_number = generate_order_number()

            customer_name = request.form['customer_name']
            customer_email = request.form['customer_email']
            customer_phone = request.form['customer_phone']
            shipping_address = request.form['shipping_address']
            shipping_city = request.form['shipping_city']
            shipping_state = request.form.get('shipping_state', '')
            shipping_zip = request.form.get('shipping_zip', '')
            payment_method = request.form['payment_method']
            notes = request.form.get('notes', '')

            # Calculate total
            total_amount = 0
            order_items = []

            for product_id, item_data in cart.items():
                product = Product.query.get(int(product_id))
                if product and product.stock >= item_data['quantity']:
                    item_total = product.price * item_data['quantity']
                    total_amount += item_total
                    order_items.append({
                        'product_id': int(product_id),
                        'quantity': item_data['quantity'],
                        'size': item_data.get('size'),
                        'color': item_data.get('color'),
                        'price': product.price
                    })
                    # Reduce stock
                    product.stock -= item_data['quantity']
                else:
                    flash(f'Product {product.name} is out of stock', 'error')
                    return redirect(url_for('cart'))

            # Create order in database
            order = Order(
                order_number=order_number,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping_address,
                shipping_city=shipping_city,
                shipping_state=shipping_state,
                shipping_zip=shipping_zip,
                total_amount=total_amount,
                payment_method=payment_method,
                notes=notes,
                status='Processing'
            )

            db.session.add(order)
            db.session.flush()  # Get order ID without committing

            # Add order items
            for item in order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    size=item['size'],
                    color=item['color'],
                    price_at_purchase=item['price']
                )
                db.session.add(order_item)

            db.session.commit()

            # Clear cart
            save_cart_to_session({})

            return redirect(url_for('order_success', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error placing order: {str(e)}', 'error')
            return redirect(url_for('checkout'))

    # GET request - show checkout form
    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * item_data['quantity']
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'size': item_data.get('size'),
                'color': item_data.get('color'),
                'subtotal': item_total
            })
            total_price += item_total

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)


@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    """Order success page"""
    order = Order.query.get_or_404(order_id)
    return render_template('success.html', order=order)


@app.route('/orders')
def orders():
    """View all orders (for demo, show all)"""
    orders_list = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders_list)


@app.route('/order/<int:order_id>')
def order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('order_detail.html', order=order)


@app.route('/admin')
def admin():
    """Admin dashboard"""
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    pending_orders = Order.query.filter_by(status='Pending').count()
    products = Product.query.all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    return render_template('admin.html',
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           pending_orders=pending_orders,
                           products=products,
                           recent_orders=recent_orders)


@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """Update order status (API)"""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()

    order.status = data.get('status', order.status)
    db.session.commit()

    return jsonify({'success': True, 'order': order.to_dict()})


@app.route('/api/products')
def api_products():
    """Get all products as JSON"""
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])


@app.route('/api/orders')
def api_orders():
    """Get all orders as JSON"""
    orders_list = Order.query.all()
    return jsonify([order.to_dict() for order in orders_list])


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


# ==================== Context Processors ====================

@app.context_processor
def inject_cart_count():
    cart = get_cart_from_session()
    cart_count = sum(item['quantity'] for item in cart.values())
    return dict(cart_count=cart_count)


@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update product quantity in cart"""
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))

    if quantity < 1:
        return redirect(url_for('remove_from_cart', product_id=product_id))

    if product.stock < quantity:
        return jsonify({'success': False, 'error': 'Insufficient stock'})

    cart = get_cart_from_session()
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str]['quantity'] = quantity
        save_cart_to_session(cart)

    return jsonify({'success': True})

# ==================== Database Initialization ====================

def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()

        # Check if products already exist
        if Product.query.first():
            return

        # Sample products
        products_data = [
            {
                'name': 'Classic Crewneck Sweatshirt',
                'description': 'Comfortable and cozy classic crewneck sweatshirt perfect for everyday wear.',
                'price': 45.99,
                'stock': 100,
                'category': 'Sweatshirts'
            },
            {
                'name': 'Premium Hoodie',
                'description': 'High-quality hoodie with drawstring and kangaroo pocket.',
                'price': 59.99,
                'stock': 80,
                'category': 'Hoodies'
            },
            {
                'name': 'Athletic Sweatpants',
                'description': 'Relaxed fit sweatpants with elastic waistband and tapered ankles.',
                'price': 39.99,
                'stock': 120,
                'category': 'Bottoms'
            },
            {
                'name': 'Zip-Up Hoodie',
                'description': 'Versatile zip-up hoodie with double pockets.',
                'price': 65.99,
                'stock': 75,
                'category': 'Hoodies'
            },
            {
                'name': 'Fleece Sweatshirt',
                'description': 'Soft fleece sweatshirt ideal for cooler weather.',
                'price': 54.99,
                'stock': 90,
                'category': 'Sweatshirts'
            },
            {
                'name': 'Running Sweatpants',
                'description': 'Lightweight sweatpants designed for active lifestyle.',
                'price': 44.99,
                'stock': 110,
                'category': 'Bottoms'
            },
            {
                'name': 'Oversized Sweatshirt',
                'description': 'Trendy oversized fit sweatshirt for maximum comfort.',
                'price': 49.99,
                'stock': 85,
                'category': 'Sweatshirts'
            },
            {
                'name': 'Color Block Hoodie',
                'description': 'Modern color-block design hoodie with contrast panels.',
                'price': 69.99,
                'stock': 60,
                'category': 'Hoodies'
            }
        ]

        for product_data in products_data:
            product = Product(**product_data)
            db.session.add(product)

        db.session.commit()
        print("Database initialized with sample products!")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)