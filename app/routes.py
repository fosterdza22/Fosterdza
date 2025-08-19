from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from .models import Product, Order

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

from . import db

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    return render_template('product_detail.html', product=product)

@bp.route('/order_history')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)

@bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    # Ensure the user can only view their own orders
    if order.user_id != current_user.id:
        abort(403)
    return render_template('order_detail.html', order=order)
