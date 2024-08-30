from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_cors import CORS
from uagents.query import query
from uagents import Model
import json
import asyncio
import re
import base64
from flask_login import LoginManager
from flask_login import UserMixin, login_user, login_required, logout_user, current_user


login_manager = LoginManager()


app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app) 

boa_agent = 'agent1qwunva6s34a58fe4dwsdvhmsjvqpw0tmp2gnxf3hy0zkzvr7x780ka9uufq'
mba_agent = 'agent1qtgnrs9umw296gtpy0h4rleeh6c6fmzlkaeuc4n9wgky2jx0gej7gc6gh7g'
ivm_agent = 'agent1qwtw7eyyzh6dmxcpdp4f6el374lugkkgxqgt3uz6r6m406526zutcs4q7nl'

class BOA_receive(Model):
    product_name: str

class MBARequest(Model):
    message:str

class MBAResponse(Model):
    results: str

class IVMRequest(Model):
    Client_Name: str
    Client_Email: str
    Client_Phone_Number: str
    Item_Name: str
    Quantity: int
    Price: int

class IVMResponse(Model):
    message: str

# In-memory user store (this should ideally be replaced with a database)
users = {
    'admin': {'password': 'password'}  # Example user
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

    @staticmethod
    def get(user_id):
        if user_id in users:
            return User(user_id)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate user credentials
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Adjust this to your desired redirect after login
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    product_offer = None 
    mba_results = None  
    product_offer_data = None
    invoice_response = None
    parsed_mba_results = [] 

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'boa':
            product_name = request.form.get('product_name')
            
            if product_name:
                try:
                    print(f"Received product name: {product_name}")
                    response = asyncio.run(query(destination=boa_agent, message=BOA_receive(product_name=product_name), timeout=15.0))
                    
                    if response is None:
                        print("Failed to receive a response from the agent.")
                        return jsonify({"error": "Failed to communicate with the agent."}), 500

                    print(f"Agent response: {response}")
                    try:
                        encoded_payload = response.payload
                        decoded_bytes = base64.b64decode(encoded_payload)
                        decoded_str = decoded_bytes.decode('utf-8')
                        product_offer = json.loads(decoded_str)
                        if isinstance(decoded_str, dict):
                            product_offer = str(decoded_str)
                        else:
                            product_offer = decoded_str
                        name = re.search(r"'name':\s*'([^']*)'", product_offer).group(1)
                        place = re.search(r"'Place':\s*'([^']*)'", product_offer).group(1)
                        price_per_unit = re.search(r"'Price_per_unit':\s*([\d.]+)", product_offer).group(1)
                        offers = re.search(r"'Offers':\s*'([^']*)'", product_offer).group(1)
                        effective_price = re.search(r"'effective_price':\s*([\d.]+)", product_offer).group(1)

                        product_offer_data = {
                            'name': name,
                            'Place': place,
                            'Price_per_unit': price_per_unit,
                            'Offers': offers,
                            'effective_price': effective_price
                        }
                    except (AttributeError, json.JSONDecodeError, base64.binascii.Error) as e:
                        print(f"Error decoding payload: {e}")
                        return jsonify({"error": "Received an invalid response from the agent."}), 500                    
                    
                    print(f"Processed data: {product_offer_data}")

                except Exception as e:
                    print(f"General error occurred: {e}")
                    return jsonify({"error": str(e)}), 500
        
        elif action == 'mba':
            min_support = request.form.get('min_support')
            min_confidence = request.form.get('min_confidence')
            min_lift = request.form.get('min_lift')
            if min_support and min_confidence and min_lift:
                try:
                    mssg = "support = " + str(min_support)+ ", confidence = " + str(min_confidence) + ", lift = " + str(min_lift)
                    print(f"Received MBA parameters: support={min_support}, confidence={min_confidence}, lift={min_lift}")
                    response = asyncio.run(query(destination=mba_agent, message=MBARequest(message=mssg), timeout=15.0))
                    
                    if response is None:
                        print("Failed to receive a response from the agent.")
                        return jsonify({"error": "Failed to communicate with the agent."}), 500

                    print(f"MBA Agent response: {response}")
                    try:
                        encoded_payload = response.payload
                        decoded_bytes = base64.b64decode(encoded_payload)
                        decoded_str = decoded_bytes.decode('utf-8')
                        mba_results = json.loads(decoded_str)
                        results_str = mba_results['results']
                        rules = results_str.split('\n')
                        rule_pattern = re.compile(r"(.+?)\s*=>\s*(.+?)\s*\|\s*Support:\s*([\d.]+),\s*Confidence:\s*([\d.]+),\s*Lift:\s*([\d.]+)")
                        for rule in rules:
                            match = rule_pattern.search(rule)
                            if match:
                                parsed_mba_results.append({
                                    'antecedent': match.group(1),
                                    'consequent': match.group(2),
                                    'support': match.group(3),
                                    'confidence': match.group(4),
                                    'lift': match.group(5)
                                })

                    except (AttributeError, json.JSONDecodeError, base64.binascii.Error) as e:
                        print(f"Error decoding MBA payload: {e}")
                        return jsonify({"error": "Received an invalid response from the agent."}), 500

                    print(f"Processed MBA data: {parsed_mba_results}")

                except Exception as e:
                    print(f"General error occurred: {e}")
                    return jsonify({"error": str(e)}), 500

        elif action == 'ivm':
            Client_Name = request.form.get('Client_Name')
            Client_Email = request.form.get('Client_Email')
            Client_Phone_Number = request.form.get('Client_Phone_Number')
            Item_Name = request.form.get('Item_Name')
            Quantity = request.form.get('Quantity')
            Price = request.form.get('Price')

            if all([Client_Name, Client_Email, Client_Phone_Number, Item_Name, Quantity, Price]):
                try:
                    print(f"Received Invoice Generation details.")
                    response = asyncio.run(query(destination=ivm_agent, message=IVMRequest(Client_Name=Client_Name, Client_Email=Client_Email, Client_Phone_Number=Client_Phone_Number, Item_Name=Item_Name, Quantity=int(Quantity), Price=int(Price)), timeout=15.0))
                    
                    if response is None:
                        print("Failed to receive a response from the agent.")
                        return jsonify({"error": "Failed to communicate with the agent."}), 500

                    print(f"IVM Agent response: {response}")
                    try:
                        encoded_payload = response.payload
                        decoded_bytes = base64.b64decode(encoded_payload)
                        decoded_str = decoded_bytes.decode('utf-8')
                        invoice_response = json.loads(decoded_str)
                    except (AttributeError, json.JSONDecodeError, base64.binascii.Error) as e:
                        print(f"Error decoding IVM payload: {e}")
                        return jsonify({"error": "Received an invalid response from the agent."}), 500

                    print(f"Processed IVM data: {invoice_response}")

                except Exception as e:
                    print(f"General error occurred: {e}")
                    return jsonify({"error": str(e)}), 500

    return render_template('index.html', product_offer=product_offer_data, parsed_mba_results=parsed_mba_results, invoice_response=invoice_response)


if __name__ == '__main__':
    app.run(debug=True)
