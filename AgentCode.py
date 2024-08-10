from uagents import Agent, Context, Model, Bureau
from uagents.setup import fund_agent_if_low
import pandas as pd
import http.client
import json
import numpy as np
from apyori import apriori
import asyncio
import nest_asyncio

import warnings

warnings.filterwarnings('ignore')

nest_asyncio.apply()

INVOICE_API_HOST = "invoice-api1.p.rapidapi.com"
INVOICE_API_KEY = "088c6a5670msh2b96f5b2c21cc02p10dce0jsne1a671ace727"
MAIL_API_HOST = "send-mail-serverless.p.rapidapi.com"
MAIL_API_KEY = "088c6a5670msh2b96f5b2c21cc02p10dce0jsne1a671ace727"

BOA_SEED_PHRASE = "BOA secret phrase"

INVOICE_API_HOST = "invoice-api1.p.rapidapi.com"
INVOICE_API_KEY = "088c6a5670msh2b96f5b2c21cc02p10dce0jsne1a671ace727"
MAIL_API_HOST = "send-mail-serverless.p.rapidapi.com"
MAIL_API_KEY = "088c6a5670msh2b96f5b2c21cc02p10dce0jsne1a671ace727"

MARKET_BASKET_SEED_PHRASE = "market basket agent secret phrase"
MARKET_BASKET_CSV_PATH = "C:/Users/aanvi/Desktop/VS_code/Python/Fetchai/Groceries_dataset.csv"
COMPILED_CSV_PATH = "C:/Users/aanvi/Desktop/VS_code/Python/Fetchai/compiled.csv"

business_info = {
    "name" : "Market Place",
    "address" : "4th Street, Hauz Khas",
    "contact_number" : "9898989898",
    "gst_number" : "7ZECCC7782R9Z1"
}
invoice_url = ""
filepaths = {"path": MARKET_BASKET_CSV_PATH}

#CLASSES 
class BOA_receive(Model):
    message:str

class BOA_answer(Model):
    result:dict

class MBA_receive(Model):
    min_support:float
    min_confidence:float
    min_lift:float

class IVM_receive(Model):
    msg:str
#HELPER FUNCTIONS
'''BOA CODE'''
import pandas as pd

data = pd.read_csv('C:/Users/aanvi/Desktop/VS_code/Python/Fetchai/compiled.csv')

def parse_offer(Offers, Price_per_unit):
    if not isinstance(Offers, str):
        Offers = str(Offers)
    if '%' in Offers:
        discount = int(Offers.split('%')[0])
        return Price_per_unit * (1 - discount / 100)
    else:
        return Price_per_unit

# Function to get the best offer for a specific fruit
def get_best_offer(fruit):
    # Filter items based on the provided fruit name
    filtered_items = data[data['name'].str.lower() == fruit.lower()]
    # Initialize an empty dictionary to store the result
    result = {}
    # Calculate the effective price for each item
    filtered_items['effective_price'] = filtered_items.apply(
        lambda row: parse_offer(row['Offers'], row['Price_per_unit']),
        axis=1
    )
    # Get the best offer by finding the item with the minimum effective price
    best_offer = filtered_items.loc[filtered_items['effective_price'].idxmin()]
    # Populate the result dictionary with the best offer details
    result['name'] = best_offer['name']
    result['Place'] = best_offer['Place']
    result['Price_per_unit'] = best_offer['Price_per_unit']
    result['Offers'] = best_offer['Offers']
    result['effective_price'] = best_offer['effective_price']
    return result
    # CAN SEND ORDER BACK TO SELLER TOO FROM MAIL


'''MBA CODE'''
def process_csv_and_generate_outputs(file_path, min_support, min_confidence, min_lift):
        min_support = float(min_support)
        min_confidence = float(min_confidence)
        min_lift = float(min_lift)
        df = pd.read_csv(file_path)
        # Customer-level data
        cust_level = df[["Member_number", "itemDescription"]].sort_values(by="Member_number", ascending=False)
        cust_level['itemDescription'] = cust_level['itemDescription'].str.strip()

        # Transactions for Apriori
        transactions = [a[1]['itemDescription'].tolist() for a in cust_level.groupby(['Member_number'])]

        # Apply Apriori algorithm
        def inspect(results):
            lhs = []
            rhs = []
            supports = []
            confidences = []
            lifts = []
            for result in results:
                if len(result[2]) > 0:
                    if len(result[2][0]) > 0:
                        lhs.append(tuple(result[2][0][0])[0] if result[2][0][0] else None)
                        rhs.append(tuple(result[2][0][1])[0] if result[2][0][1] else None)
                        supports.append(result[1])
                        confidences.append(result[2][0][2] if len(result[2][0]) > 2 else None)
                        lifts.append(result[2][0][3] if len(result[2][0]) > 3 else None)
            return list(zip(lhs, rhs, supports, confidences, lifts))
        def perform_apriori_analysis(transactions, min_support, min_confidence, min_lift):
            rules = apriori(transactions=transactions, min_support=min_support, min_confidence=min_confidence, min_lift=min_lift, min_length=2, max_length=2)
            results = list(rules)
            results_df = pd.DataFrame(inspect(results), columns=['Left Hand Side', 'Right Hand Side', 'Support', 'Confidence', 'Lift'])
            results_df['Lift'] = pd.to_numeric(results_df['Lift'])
            results_df = results_df.nlargest(n=5, columns="Lift")
            return results_df
        results_df = perform_apriori_analysis(transactions, min_support, min_confidence, min_lift)
        return transactions, results_df

'''IVM CODE'''
async def generate_new_invoice(ctx: Context):
    global invoice_url
    conn = http.client.HTTPSConnection(INVOICE_API_HOST)

    # Collect client and items information
    print("Please enter client information:")
    client_name = input("Client Name: ")
    client_email = input("Client Email: ")
    client_phone = input("Client Phone Number: ")

    items = []
    while True:
        item_name = input("Item Name (or type 'done' to finish): ")
        if item_name.lower() == 'done':
            break
        item_quantity = int(input("Quantity: "))
        item_price = float(input("Price: "))
        items.append({
            "name": item_name,
            "quantity": item_quantity,
            "description": "No description",  # Default description
            "price": item_price
        })

    payload = json.dumps({
        "invoice_number": "INV-00202",
        "issued_at": "2024-03-26",
        "due_at": "2024-03-26",
        "currency_code": "INR",
        "notes": "This is note for invoice",
        "company": {
            "name": business_info["name"],
            "tax_number": business_info["gst_number"],
            "address": business_info["address"],
            "contact_number": business_info["contact_number"],
            "email": "info@mycompany.com",  # Default email or use a variable
            "logo_url": "https://example.com/logo.jpg"  # Default logo URL or use a variable
        },
        "customer": {
            "name": client_name,
            "email": client_email,
            "address": "Client address",  # You might want to collect address separately
            "tax_number": ""  # GST number for customer if applicable
        },
        "consignee": {
            "name": client_name,
            "email": client_email,
            "address": "Client address"
        },
        "items": items,
        "footer": "This is footer for invoice",
        "mail_to": client_email
    })

    headers = {
        'x-rapidapi-key': INVOICE_API_KEY,
        'x-rapidapi-host': INVOICE_API_HOST,
        'Content-Type': "application/json"
    }

    conn.request("POST", "/createInvoice", payload, headers)
    res = conn.getresponse()
    data = res.read()
    response = json.loads(data)

    # Extract the invoice URL from the response
    invoice_url = response.get("data", {}).get("invoice_url", "")

    # Check if the invoice URL is available
    if invoice_url:
        formatted_data = json.dumps(response, indent=4)
        print("Invoice generated successfully:")
        print(formatted_data)
        
        # Send the invoice PDF to the client
        await send_invoice_to_client(ctx, client_email, invoice_url)
    else:
        print("Invoice URL not available. Unable to send email.")

async def get_all_invoices(ctx: Context):
    conn = http.client.HTTPSConnection(INVOICE_API_HOST)

    headers = {
        'x-rapidapi-key': INVOICE_API_KEY,
        'x-rapidapi-host': INVOICE_API_HOST
    }

    conn.request("GET", "/getAllInvoices", headers=headers)
    res = conn.getresponse()
    data = res.read()
    formatted_data = json.dumps(json.loads(data), indent=4)
    print("All invoices:")
    print(formatted_data)

async def get_invoice_by_id(ctx: Context, invoice_id: str):
    conn = http.client.HTTPSConnection(INVOICE_API_HOST)

    headers = {
        'x-rapidapi-key': INVOICE_API_KEY,
        'x-rapidapi-host': INVOICE_API_HOST
    }

    conn.request("GET", f"/getInvoice/{invoice_id}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    formatted_data = json.dumps(json.loads(data), indent=4)
    print(f"Invoice details for ID {invoice_id}:")
    print(formatted_data)

async def send_invoice_to_client(ctx: Context, client_email: str, invoice_url: str):
    conn = http.client.HTTPSConnection(MAIL_API_HOST)

    payload = json.dumps({
        "personalizations": [{
            "to": [{
                "email": client_email,
                "name": "Customer"
            }]
        }],
        "from": {
            "email": "test@firebese.com",
            "name": "Market Place"
        },
        "reply_to": {
            "email": "test@firebese.com",
            "name": "Market Place"
        },
        "subject": "Thank you for your order !",
        "content": [{
            "type": "text/html",
            "value": f"Dear Customer,<br><br>Please find your invoice attached below.<br><br>Invoice URL: <a href='{invoice_url}'>{invoice_url}</a><br><br>Thank you for your order.<br><br>Best Regards,<br>Dominos"
        }],
        "headers": {
            "List-Unsubscribe": "<mailto: unsubscribe@firebese.com?subject=unsubscribe>, <https://firebese.com/unsubscribe/id>"
        }
    })

    headers = {
        'x-rapidapi-key': MAIL_API_KEY,
        'x-rapidapi-host': MAIL_API_HOST,
        'Content-Type': 'application/json'
    }

    conn.request("POST", "/send", payload, headers)
    res = conn.getresponse()
    data = res.read()
    response = json.loads(data)
    
    formatted_data = json.dumps(response, indent=4)
    print("Mail sending response:")
    print(formatted_data)
    
#AGENTS
BOA = Agent(
    name="BOA",
    port=8001,
    seed="BOA secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)

fund_agent_if_low(BOA.wallet.address())

MBA = Agent(
    name="market_basket_agent",
    port=8002,
    seed="market basket agent secret phrase",
    endpoint=["http://localhost:8002/analyze"],
)
fund_agent_if_low(MBA.wallet.address())

IVM = Agent(
    name="Invoice",
    port=8003,
    seed="user secret phrase",
    endpoint=["http://localhost:8003/submit"],
)
fund_agent_if_low(IVM.wallet.address())

user = Agent(
    name="user",
    port=8004,
    seed="user secret phrase",
    endpoint=["http://127.0.0.1:8004/submit"],
)
fund_agent_if_low(user.wallet.address())

@user.on_event('startup')
async def startup(ctx: Context):
    print(f"User Agent address: {user.address}")
    print(f"BOA Agent address: {BOA.address}")
    print(f"MBA Agent address: {MBA.address}")

@user.on_interval(period=100.0)
async def interval_user(ctx: Context):
    print("Select an option:")
    print("1. Request Best Offer")
    print("2. Perform Market Basket Analysis")
    print("3. Invoice Related")
    choice = input("Enter your choice: ")
    if choice == '1':
        product_name = input("Enter the Product name: ")
        await ctx.send(BOA.address, BOA_receive(message=product_name))
    elif choice == '2':
        ms = float(input('Enter minimum support value (e.g., 0.01): '))
        mc = float(input('Enter minimum confidence value (e.g., 0.6): '))
        ml = float(input('Enter minimum lift value (e.g., 1.5): '))
        await ctx.send(MBA.address, MBA_receive(min_confidence=mc, min_support=ms, min_lift=ml))
    elif choice == '3':
        await ctx.send(IVM.address, IVM_receive(msg="YOUR WORK HAH"))


@BOA.on_message(model=BOA_receive)
async def BOA_msg_handler(ctx: Context, sender: str, msg: BOA_receive):
    ctx.logger.info(f"Received msg from {sender}")
    print("BOA agent started")
    best_offer = get_best_offer(msg.message)
    print(best_offer)  


@MBA.on_message(model=MBA_receive)
async def MBA_msg_handler(ctx: Context, sender:str, msg: MBA_receive):
    global filepaths
    file_path = filepaths.get("path")
    if not file_path:
        ctx.logger.error("File path not provided.")
        return
    transactions, results_df = process_csv_and_generate_outputs(file_path, msg.min_support, msg.min_confidence, msg.min_lift)
    ctx.logger.info("Apriori analysis completed successfully.")
    ctx.logger.info(f"Results DataFrame: \n{results_df}")

@IVM.on_message(model=IVM_receive)
async def BOA_msg_handler(ctx: Context, sender: str, msg: IVM_receive):
    ctx.logger.info(f"Received msg from {sender}")
    print("Options:")
    print("1. Generate new invoice")
    print("2. Get all invoices")
    print("3. Get invoice by ID")
    choice = int(input("Choose an option (1-3): "))
    if choice == 1:
        await generate_new_invoice(ctx)
    elif choice == 2:
        await get_all_invoices(ctx)
    elif choice == 3:
        invoice_id = input("Enter the invoice ID: ")
        await get_invoice_by_id(ctx, invoice_id)
    else:
        print("Invalid choice. Please choose a valid option.")

bureau = Bureau()
bureau.add(user)
bureau.add(BOA)
bureau.add(MBA)
bureau.add(IVM)

bureau.run()