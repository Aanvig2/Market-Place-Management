from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
import pandas as pd
from ai_engine import UAgentResponse, UAgentResponseType

# Define the model for receiving messages related to Best Offer Analysis
class BOARequest(Model):
    message: str

# Define the seed phrase for the BOA Agent
SEED_PHRASE = "boacodeeeeeeeeeee"

# Initialize the BOA agent with its configuration
boa_agent = Agent(
    name="Best Offer Agent",
    port=8001,
    seed=SEED_PHRASE,
    endpoint=["http://127.0.0.1:8001/submit"],
    mailbox="42c5a797-11fe-4737-ab3f-6929151510e5@https://agentverse.ai"
)

# Ensure the agent has enough funds
fund_agent_if_low(boa_agent.wallet.address())

# Print the agent's address on startup
@boa_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(boa_agent.address)

# Load data for Best Offer Analysis
data = pd.read_csv('C:/Users/aanvi/Desktop/VS_code/Python/final_project/backend/compiled.csv')

# Helper function to parse offer and calculate effective price
def parse_offer(Offers, Price_per_unit):
    if not isinstance(Offers, str):
        Offers = str(Offers)
    if '%' in Offers:
        discount = int(Offers.split('%')[0])
        return Price_per_unit * (1 - discount / 100)
    else:
        return Price_per_unit

# Helper function to get the best offer for a product
def get_best_offer(product):
    filtered_items = data[data['name'].str.lower() == product.lower()]
    result = {}
    filtered_items['effective_price'] = filtered_items.apply(
        lambda row: parse_offer(row['Offers'], row['Price_per_unit']),
        axis=1
    )
    best_offer = filtered_items.loc[filtered_items['effective_price'].idxmin()]
    result['name'] = best_offer['name']
    result['Place'] = best_offer['Place']
    result['Price_per_unit'] = best_offer['Price_per_unit']
    result['Offers'] = best_offer['Offers']
    result['effective_price'] = best_offer['effective_price']
    return result

# Protocol to handle Best Offer Analysis requests
boa_protocol = Protocol("Best Offer Analysis Protocol")

# Define the event handler for BOA requests
@boa_protocol.on_message(model=BOARequest, replies={UAgentResponse})
async def boa_msg_handler(ctx: Context, sender: str, msg: BOARequest):
    product_name = msg.message
    best_offer = get_best_offer(product_name)
    ctx.logger.info("Best offer calculation completed successfully.")
    message = f"Best offer details:\n{best_offer}"
    await ctx.send(sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL))

# Include the protocol in the agent and run the agent
boa_agent.include(boa_protocol, publish_manifest=True)
boa_agent.run()
