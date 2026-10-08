import os
from http.client import responses

import httpx
from typing import Optional
from uuid import uuid4

from charset_normalizer.cd import coherence_ratio
from httpx2 import query
from langchain_core.tools import tool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv(verbose=True)

API_URL = "https://hopscotch-shop.vercel.app"

email = input("Your shopping email: ").strip()

response = httpx.post(f'{API_URL}/auth/login',
                      json={"email": email},
                      timeout=30
                      )


response.raise_for_status()
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

@tool
def get_Cart() -> dict:
    """Inspect the signed-in customer's current cart.
    Use for questions about cart contents , quantities and totals.
    Takes no arguments. Returns the current cart items and totals.
    Money values are integer paise: 100 paise equals 1 INR.

    This tool only reads the cart; it cannot edit or place order."""

    response = httpx.get(f'{API_URL}/cart',
                      headers=headers,
                      timeout=30
                      )
    response.raise_for_status()
    cart_items = response.json()
    return cart_items

llm = ChatOpenAI(
    model = "google/gemini-2.5-flash",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0
)

query = "What is the weather like in Dubai right now ?"
response = llm.invoke(query)
print(response.content)

query = """Imagine you are weather agent, your only job is to tell me if I need to call function weather_func(city)\
which is already available to me, I will call the function and give you the output of the function and then you can\
give final answer, if the question is not related to weather answer normally.
Query - What is the weather like in Dubai right now?"""

response = llm.invoke(query)
print(response.content)

def weather_func(city):
    return 32

output = weather_func("Dubai")
print(output)

new_query = query +  response.content + f"Function output: {output}"
new_response = llm.invoke(new_query)
print(new_response.content)

@tool
def get_city_weather(city: str):
    """
    Fetches the current weather conditions for specified city.
    Use this tool whenever a user asks about the weather, temperature,
    or humidity in a specific location.

    Args:
        city (str): The name of city to check the weather for.

        Examples: "Delhi", "Mumbai", "Bengaluru", "Chicago"

    Returns:
        dict: A dictionary containing the weather details with the following keys:
            - temperature (int): The current temperature in Celsius.
            - humidity (int): The current humidity in percentage.
            - condition(str): The current weather condition.(e.g. , "Hot", "Humid", "Pleasant",
            "unknown")
    """

    fake_weather_db = {
        "Delhi" : {"temperature" : 34, "humidity" : 35, "condition" : "Hot"},
        "Mumbai" : {"temperature" : 34, "humidity" : 55, "condition" : "Humid"},
        "Bengaluru" : {"temperature" : 32, "humidity" : 25, "condition" : "Pleasant"},
    }

    return fake_weather_db.get(city, {"temperature" : 32, "humidity" : 25, "condition" : "unknown"})


duckduckgo_search = DuckDuckGoSearchRun()

get_city_weather.invoke({"city" : "Delhi"})

response = duckduckgo_search.invoke({"query": "What is the situation in Goa right now?"})
print(response)