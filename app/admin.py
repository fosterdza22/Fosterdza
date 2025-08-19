from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from .forms import ProductForm
from .models import Product
from . import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def index():
    return redirect(url_for('admin.products'))

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/product/new', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Price is submitted in GHS, convert to pesewas
        price_in_pesewas = int(form.price.data * 100)
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=price_in_pesewas
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully.')
        return redirect(url_for('admin.products'))
    return render_template('admin/add_product.html', form=form)

@admin_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    # Price is stored in pesewas, convert to GHS for the form
    form = ProductForm(obj=product, price=product.price / 100.0)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = int(form.price.data * 100)
        db.session.commit()
        flash('Product updated successfully.')
        return redirect(url_for('admin.products'))
    return render_template('admin/edit_product.html', form=form, product=product)

@admin_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('admin.products'))
