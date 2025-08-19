from flask import Blueprint, render_template, redirect, url_for, session, request, flash, current_app
from flask_login import login_required, current_user
import requests
from .models import Product, Order, OrderItem
from . import db

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/')
@login_required
def index():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.')
        return redirect(url_for('main.index'))

    # Create Order in the database
    order = Order(user_id=current_user.id)
    db.session.add(order)

    total_price = 0
    for product_id, item_data in cart.items():
        product = Product.query.get(product_id)
        if product:
            quantity = item_data['quantity']
            price = product.price * quantity
            total_price += price
            order_item = OrderItem(
                order=order,
                product_id=product.id,
                quantity=quantity,
                price=product.price
            )
            db.session.add(order_item)

    # Initialize Paystack payment
    headers = {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }
    data = {
        "email": current_user.email,
        "amount": total_price,
        "currency": "GHS",
        "callback_url": url_for('checkout.callback', _external=True),
        "metadata": {
            "order_id": order.id,
        }
    }

    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
        response_data = response.json()
        if response_data['status']:
            # Before redirecting, commit the order to the DB
            db.session.commit()
            order.paystack_reference = response_data['data']['reference']
            db.session.commit()
            # Clear the cart
            session.pop('cart', None)
            return redirect(response_data['data']['authorization_url'])
        else:
            db.session.rollback()
            flash(f"Error initializing payment: {response_data['message']}")
            return redirect(url_for('cart.view_cart'))
    except requests.exceptions.RequestException as e:
        db.session.rollback()
        flash(f"An error occurred: {e}")
        return redirect(url_for('cart.view_cart'))


@checkout_bp.route('/callback')
def callback():
    reference = request.args.get('reference')
    if not reference:
        return render_template('payment_failure.html', message="No payment reference provided.")

    headers = {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
    }

    try:
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        response_data = response.json()

        if response_data['status']:
            if response_data['data']['status'] == 'success':
                order_id = response_data['data']['metadata'].get('order_id')
                order = Order.query.get(order_id)
                if order:
                    order.is_paid = True
                    db.session.commit()
                    return render_template('payment_success.html', order=order)
                else:
                    return render_template('payment_failure.html', message="Order not found.")
            else:
                return render_template('payment_failure.html', message="Payment was not successful.")
        else:
            return render_template('payment_failure.html', message=f"Error verifying payment: {response_data['message']}")
    except requests.exceptions.RequestException as e:
        return render_template('payment_failure.html', message=f"An error occurred: {e}")
