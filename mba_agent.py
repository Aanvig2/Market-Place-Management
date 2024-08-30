from uagents import Agent, Context, Model, Protocol
from uagents.setup import fund_agent_if_low
import pandas as pd
from apyori import apriori

# Define models for receiving and replying to Market Basket Analysis requests
class MBARequest(Model):
    message: str  # Now uses a single message field to receive the parameters

class MBAResponse(Model):
    results: str

class ErrorResponse(Model):
    error: str

# Initialize the MBA agent
MBA_agent = Agent(
    name="Market Basket Agent",
    port=8002,
    seed="mbaaasecret",
    endpoint=["http://localhost:8002/submit"]
)

# Ensure the agent has enough funds
fund_agent_if_low(MBA_agent.wallet.address())

# Print the agent's address on startup
@MBA_agent.on_event('startup')
async def on_startup(ctx: Context):
    ctx.logger.info(MBA_agent.address)

# Helper function to extract parameters from the message string
def extract_parameters(message):
    try:
        # Extract parameters using string operations
        params = {}
        for param in message.split(','):
            key, value = param.split('=')
            params[key.strip()] = float(value.strip())
        return params['support'], params['confidence'], params['lift']
    except Exception as e:
        raise ValueError(f"Failed to extract parameters: {e}")

# Helper function to process CSV and perform Market Basket Analysis
async def perform_mba_analysis(min_support, min_confidence, min_lift):
    file_path = "C:/Users/aanvi/Desktop/VS_code/Python/final_project/backend/Groceries_dataset.csv"
    df = pd.read_csv(file_path)

    cust_level = df[["Member_number", "itemDescription"]].sort_values(by="Member_number", ascending=False)
    cust_level['itemDescription'] = cust_level['itemDescription'].str.strip()
    
    transactions = [a[1]['itemDescription'].tolist() for a in cust_level.groupby(['Member_number'])]
    
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

    rules = apriori(transactions=transactions, min_support=min_support, min_confidence=min_confidence, min_lift=min_lift, min_length=2, max_length=2)
    results = list(rules)
    results_df = pd.DataFrame(inspect(results), columns=['Left Hand Side', 'Right Hand Side', 'Support', 'Confidence', 'Lift'])
    results_df['Lift'] = pd.to_numeric(results_df['Lift'])
    results_df = results_df.nlargest(n=5, columns="Lift")
    
    formatted_results = ""
    for index, row in results_df.iterrows():
        formatted_results += f"{row['Left Hand Side']} => {row['Right Hand Side']} | Support: {row['Support']:.4f}, Confidence: {row['Confidence']:.4f}, Lift: {row['Lift']:.4f}\n"
    
    return formatted_results

# Protocol to handle MBA requests
MBA_protocol = Protocol("Market Basket Analysis Protocol")

@MBA_agent.on_query(model=MBARequest, replies=MBAResponse)
async def mba_msg_handler(ctx: Context, sender: str, msg: MBARequest):
    try:
        ctx.logger.info(f'Received MBA request: {msg.message}')
        
        # Extract parameters from the message string
        min_support, min_confidence, min_lift = extract_parameters(msg.message)
        ctx.logger.info(f'Extracted parameters - Support: {min_support}, Confidence: {min_confidence}, Lift: {min_lift}')
        
        # Perform Apriori analysis with extracted parameters
        results = await perform_mba_analysis(min_support, min_confidence, min_lift)
        ctx.logger.info(f'Apriori analysis completed successfully with results: {results}')

        # Send the results back to the sender
        await ctx.send(sender, MBAResponse(results=str(results)))

    except ValueError as ve:
        ctx.logger.error(f'Parameter extraction error: {ve}')
        await ctx.send(sender, ErrorResponse(error=f"Parameter extraction error: {ve}"))
    except Exception as e:
        ctx.logger.error(f'Error processing request: {e}')
        await ctx.send(sender, ErrorResponse(error="Error"))

# Include the protocol in the agent and run the agent
MBA_agent.include(MBA_protocol, publish_manifest=True)

if __name__ == "__main__":
    MBA_agent.run()
