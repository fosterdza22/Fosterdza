from flask import Flask, render_template, request, redirect, url_for
import requests
import os

app = Flask(__name__)

# In a real application, get these from a secure location
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'YOUR_PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', 'YOUR_PAYSTACK_PUBLIC_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pay', methods=['POST'])
def pay():
    # In a real app, you'd get the amount and email from a form or database
    amount = 10000  # in pesewas (100 GHS)
    email = "customer@example.com"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": email,
        "amount": amount,
        "currency": "GHS",
        "callback_url": url_for('callback', _external=True),
        "channels": ['mobile_money']
    }

    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
        response_data = response.json()
        if response_data['status']:
            return redirect(response_data['data']['authorization_url'])
        else:
            return f"Error: {response_data['message']}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


@app.route('/callback')
def callback():
    reference = request.args.get('reference')
    if not reference:
        return "Error: No reference provided"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }

    try:
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        response_data = response.json()

        if response_data['status']:
            if response_data['data']['status'] == 'success':
                return "Payment successful!"
            else:
                return "Payment failed."
        else:
            return f"Error: {response_data['message']}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    app.run(debug=True)
