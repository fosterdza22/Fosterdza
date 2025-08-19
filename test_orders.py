import pytest
from app import create_app, db
from app.models import User, Product, Order, OrderItem
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///:memory:'
    })

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def login(client, email, password):
    return client.post('/auth/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def test_order_history(client):
    with client.application.app_context():
        # Setup data for this specific test
        hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
        customer = User(email='customer@example.com', password=hashed_password)
        db.session.add(customer)
        p1 = Product(name='Camera', description='A camera.', price=100)
        db.session.add(p1)
        order = Order(user=customer, is_paid=True)
        db.session.add(order)
        item = OrderItem(order=order, product=p1, quantity=1, price=p1.price)
        db.session.add(item)
        db.session.commit()

    login(client, 'customer@example.com', 'password123')
    response = client.get('/order_history')
    assert response.status_code == 200
    assert b'Your Order History' in response.data
    assert b'<td>1</td>' in response.data

def test_order_detail(client):
    with client.application.app_context():
        # Setup data for this specific test
        hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
        customer = User(email='customer@example.com', password=hashed_password)
        db.session.add(customer)
        p1 = Product(name='Camera', description='A camera.', price=100)
        db.session.add(p1)
        order = Order(user=customer, is_paid=True)
        db.session.add(order)
        item = OrderItem(order=order, product=p1, quantity=1, price=p1.price)
        db.session.add(item)
        db.session.commit()

    login(client, 'customer@example.com', 'password123')
    response = client.get('/order/1')
    assert response.status_code == 200
    assert b'Order #1' in response.data
    assert b'Camera' in response.data

def test_unauthorized_order_access(client):
    with client.application.app_context():
        # Setup data for this specific test
        hashed_password_owner = generate_password_hash('pass_owner', method='pbkdf2:sha256')
        owner = User(email='owner@example.com', password=hashed_password_owner)
        hashed_password_other = generate_password_hash('pass_other', method='pbkdf2:sha256')
        other = User(email='other@example.com', password=hashed_password_other)
        db.session.add_all([owner, other])

        p1 = Product(name='Camera', description='A camera.', price=100)
        db.session.add(p1)
        order = Order(user=owner, is_paid=True)
        db.session.add(order)
        item = OrderItem(order=order, product=p1, quantity=1, price=p1.price)
        db.session.add(item)
        db.session.commit()

    login(client, 'other@example.com', 'pass_other')
    response = client.get('/order/1')
    assert response.status_code == 403
