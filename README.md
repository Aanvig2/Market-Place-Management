# uAgent Market Place Management

This repository contains a Market Place Management network using four agents: `BOA`(Best Offer Analysis Agent), `MBA` (Market Basket Analysis Agent), `IVM`(Invoice and Mailing agent) and `User` Agent.

**`User` Agent** - Allows the user to choose between different options: requesting the best offer (`BOA` agent), performing market basket analysis (`MBA` agent), or handling invoice-related tasks (`IVM` agent).

**`BOA` Agent** - Receives a product name from the `User` agent, calculates the best offer by finding the product with the lowest effective price (considering any discounts), and returns this information.

**`MBA` Agent** - Receives minimum support, confidence, and lift values from the `User` agent, processes the market basket data from the `Groceries_dataset.csv` file, and returns the results of the Apriori analysis, including association rules with support, confidence, and lift metrics.

**`IVM` Agent** - Handles requests related to invoices, such as generating a new invoice, retrieving all invoices, or getting an invoice by ID. It interacts with the `invoice-api1.p.rapidapi.com` to create and manage invoices and with the `send-mail-serverless.p.rapidapi.com` to send invoice emails to clients.

## How to get Started!
### Step 1: Get API Keys

**Invoice API**
1.  Visit the RapidAPI website: https://rapidapi.com/streamifyworld/api/invoice-api1
2.  If you don’t have an account, create one by signing up.
3.  Once logged in, click on “Test Endpoint” and subscribe to the API (free tier is available).
4.  After subscription, you'll receive an `x-rapidapi-key` in the header parameters.

**Mail API** 

1.  Visit the RapidAPI website: https://rapidapi.com/firebese-firebese-default/api/send-mail-serverless
2.  If you don’t have an account, create one by signing up.
3.  Once logged in, click on “Test Endpoint” and subscribe to the API (free tier is available).
4.  After subscription, you'll receive an `x-rapidapi-key` in the header parameters.

### Step 2: Set API Keys and File Paths in Agent Scripts

1.  **Update API Keys**:
    
    -   Open your script and locate the sections where the API keys are defined.
    -   Replace `INVOICE_API_KEY` and `MAIL_API_KEY` with the keys obtained from the respective APIs.
2.  **Update File Paths**:

    -   Ensure the paths to your CSV files (e.g., `MARKET_BASKET_CSV_PATH` and `COMPILED_CSV_PATH`) are correctly set in your script.
4.  **Verify Agent Endpoints**:
    
    -   Check the endpoints for each agent (`BOA`, `MBA`, `IVM`, `user`) and ensure they match your configuration.

### Step 3: Run Project

To run the project and its agents

cd AgentsFinal
python Agentcode.py

#Flask Frontend Project
1. Put index.html and login.html in templates folder
2. Install Requirements.txt
3. Run boa_agent.py, mba_agent.py and ivm_agent.py before running App.py
