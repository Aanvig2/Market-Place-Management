from uagents import Agent, Context, Model, Protocol
from uagents.setup import fund_agent_if_low
import requests
import os
import pandas as pd
import json


class BOA_receive(Model):
    product_name:str

class BOA_answer(Model):
    product_offer:str

class Error_response(Model):
    error : str

data = pd.read_csv('C:/Users/aanvi/Desktop/VS_code/Python/final_project/backend/compiled.csv')

def parse_offer(Offers, Price_per_unit):
    if not isinstance(Offers, str):
        Offers = str(Offers)
    if '%' in Offers:
        discount = int(Offers.split('%')[0])
        return Price_per_unit * (1 - discount / 100)
    else:
        return Price_per_unit

async def get_best_offer(product):
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

BOA_agent = Agent(
    name="BOA",
    port=8001,
    seed="BOA secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)

fund_agent_if_low(BOA_agent.wallet.address())

@BOA_agent.on_event('startup')
async def agent_details(ctx:Context):
    ctx.logger.info(BOA_agent.address)

@BOA_agent.on_query(model=BOA_receive, replies=BOA_answer)
async def query_handler(ctx: Context, sender: str, msg: BOA_receive):
    try:
        ctx.logger.info(f'Received message: {msg}')
        ctx.logger.info(f'Fetching Product Name: {msg.product_name}')

        best_offer = await get_best_offer(msg.product_name)
        ctx.logger.info(f'Best offer data: {best_offer}')

        await ctx.send(sender, BOA_answer(product_offer=str(best_offer)))

    except Exception as e:
        ctx.logger.error(f'Error processing request: {e}')
        await ctx.send(sender, Error_response(error="Error"))

if __name__ == "__main__":
    BOA_agent.run() 
