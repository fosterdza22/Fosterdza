from flask import Blueprint, render_template, redirect, url_for, session, request, flash, abort
from .models import Product
from . import db

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/')
def view_cart():
    cart = session.get('cart', {})
    products_in_cart = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = db.session.get(Product, product_id)
        if product:
            quantity = item_data['quantity']
            price = product.price * quantity
            total_price += price
            products_in_cart.append({
                'product': product,
                'quantity': quantity,
                'price': price
            })

    return render_template('cart.html', products_in_cart=products_in_cart, total_price=total_price)

@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    quantity = int(request.form.get('quantity', 1))

    cart = session.get('cart', {})

    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str]['quantity'] += quantity
    else:
        cart[product_id_str] = {'quantity': quantity}

    session['cart'] = cart
    flash(f'{product.name} has been added to your cart.')
    return redirect(request.referrer or url_for('main.index'))

@cart_bp.route('/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    quantity = int(request.form.get('quantity'))
    cart = session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        if quantity > 0:
            cart[product_id_str]['quantity'] = quantity
        else:
            # Remove item if quantity is 0 or less
            del cart[product_id_str]

    session['cart'] = cart
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remove/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    session['cart'] = cart
    return redirect(url_for('cart.view_cart'))
