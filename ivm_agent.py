from uagents import Agent, Context, Model, Protocol
from uagents.setup import fund_agent_if_low
import http.client
import json

# Define models for receiving and replying to Invoice Management requests
class IVMRequest(Model):
    Client_Name: str
    Client_Email: str
    Client_Phone_Number: str
    Item_Name: str
    Quantity: int
    Price: int

class IVMResponse(Model):
    message: str

class ErrorResponse(Model):
    error: str

# API Keys and Host Configuration
INVOICE_API_HOST = "invoice-api1.p.rapidapi.com"
INVOICE_API_KEY = "209946a9fbmshb80116b5b981cfep142f18jsn86a977fc9965"
MAIL_API_HOST = "send-mail-serverless.p.rapidapi.com"
MAIL_API_KEY = "209946a9fbmshb80116b5b981cfep142f18jsn86a977fc9965"

# Business information
business_info = {
    "name": "Market Place",
    "address": "4th Street, Hauz Khas",
    "contact_number": "9898989898",
    "gst_number": "7ZECCC7782R9Z1"
}

# Initialize the IVM agent
IVM_agent = Agent(
    name="Invoice Management Agent",
    port=8007,
    seed="ivmcodeeeee",
    endpoint=["http://127.0.0.1:8007/submit"]
)

# Ensure the agent has enough funds
fund_agent_if_low(IVM_agent.wallet.address())

# Print the agent's address on startup
@IVM_agent.on_event('startup')
async def agent_details(ctx: Context):
    ctx.logger.info(IVM_agent.address)

# Helper function to generate a new invoice
async def generate_new_invoice(client_name, client_email, client_phone, item_name, item_quantity, item_price):
    conn = http.client.HTTPSConnection(INVOICE_API_HOST)
    items = [{
        "name": item_name,
        "quantity": item_quantity,
        "description": "No description",
        "price": item_price
    }]

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
            "email": "info@mycompany.com",
            "logo_url": "https://example.com/logo.jpg"
        },
        "customer": {
            "name": client_name,
            "email": client_email,
            "address": "Client address",
            "tax_number": ""
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
    
    if res.status != 200:
        return f"Failed to generate invoice. Status Code: {res.status}, Reason: {res.reason}"

    data = res.read()

    try:
        response = json.loads(data)
    except json.JSONDecodeError:
        return "Failed to decode JSON response from the API."

    invoice_url = response.get("data", {}).get("invoice_url")

    if invoice_url:
        result = send_invoice_to_client(client_email, invoice_url)
        return result
    else:
        return "Invoice URL not available. Unable to send email."

# Helper function to send an invoice to the client
def send_invoice_to_client(client_email: str, invoice_url: str):
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
        "subject": "Thank you for your order!",
        "content": [{
            "type": "text/html",
            "value": f"Dear Customer,<br><br>Please find your invoice attached below.<br><br>Invoice URL: <a href='{invoice_url}'>{invoice_url}</a><br><br>Thank you for your order.<br><br>Best Regards,<br>Market Place"
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
    
    return json.dumps(response, indent=4)

# Protocol to handle Invoice Management requests
IVM_protocol = Protocol("Invoice Management Protocol")

@IVM_agent.on_query(model=IVMRequest, replies=IVMResponse)
async def ivm_msg_handler(ctx: Context, sender: str, msg: IVMRequest):
    try:
        # Log the received message
        ctx.logger.info(f'Received invoice request: {msg}')
        
        # Generate the invoice and prepare the response
        result = await generate_new_invoice(
            msg.Client_Name, msg.Client_Email, msg.Client_Phone_Number,
            msg.Item_Name, msg.Quantity, msg.Price
        )
        
        # Send the response back to the sender
        await ctx.send(sender, IVMResponse(message=result))
        
    except Exception as e:
        # Log any errors
        ctx.logger.error(f'Error processing request: {e}')
        await ctx.send(sender, ErrorResponse(error="Error"))

# Include the protocol in the agent and run the agent
IVM_agent.include(IVM_protocol, publish_manifest=True)

if __name__ == "__main__":
    IVM_agent.run()
