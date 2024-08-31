from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
import http.client
import json
from ai_engine import UAgentResponse, UAgentResponseType

# Define API Keys and Host for Invoice and Mail Services
INVOICE_API_HOST = "invoice-api1.p.rapidapi.com"
INVOICE_API_KEY = ""
MAIL_API_HOST = "send-mail-serverless.p.rapidapi.com"
MAIL_API_KEY = ""

# Business information
business_info = {
    "name": "Market Place",
    "address": "4th Street, Hauz Khas",
    "contact_number": "9898989898",
    "gst_number": "7ZECCC7782R9Z1"
}

class IVMRequest(Model):
    Client_Name: str
    Client_Email: str
    Client_Phone_Number: str
    Item_Name: str
    Quantity: int
    Price: int

# Define the seed phrase for the IVM Agent
SEED_PHRASE = "ivmcodeeeeeeee"

# Initialize the IVM agent with its configuration
ivm_agent = Agent(
    name="Invoice Management Agent",
    port=8007,
    seed=SEED_PHRASE,
    endpoint=["http://127.0.0.1:8007/submit"],
    mailbox="0af2ada7-3152-4780-aa09-061eefef6061@https://agentverse.ai"
)
# Ensure the agent has enough funds
fund_agent_if_low(ivm_agent.wallet.address())

# Print the agent's address on startup
@ivm_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"{ivm_agent.address}")

# Helper function to generate a new invoice
def generate_new_invoice(client_name, client_email, client_phone, item_name, item_quantity, item_price):
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
            formatted_data = json.dumps(response, indent=4)
            return f"Invoice generated successfully:\n{formatted_data}"
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
ivm_protocol = Protocol("Invoice Management Protocol")

@ivm_protocol.on_message(model=IVMRequest, replies={UAgentResponse})
async def ivm_msg_handler(ctx: Context, sender: str, msg: IVMRequest):
    result = generate_new_invoice(msg.Client_Name, msg.Client_Email,  msg.Client_Phone_Number, msg.Item_Name, msg.Quantity, msg.Price)
    await ctx.send(sender, UAgentResponse(message=result, type=UAgentResponseType.FINAL))


# Include the protocol in the agent and run the agent
ivm_agent.include(ivm_protocol, publish_manifest=True)
ivm_agent.run()
