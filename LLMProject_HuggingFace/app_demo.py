import os
from getpass import getpass
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

def _looks_like_hf_token(token):
    return isinstance(token, str) and len(token) > 0 and token.strip().startswith("hf_")

load_dotenv(verbose=True)
if _looks_like_hf_token(os.environ.get("HF_TOKEN")):
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        print(f"HF_TOKEN: {hf_token}")
else:
    hf_token = getpass("HF_TOKEN: ")
    print(f"HF_TOKEN: {hf_token}")

assert os.environ.get("HF_TOKEN").startswith("hf_"),("Your Token still doesn't look good"
                                                     "It should start with hf")

client = InferenceClient(provider="auto" , # let hugging face route to provider that supports this model
                         api_key=os.environ.get("HF_TOKEN"))

# The LLM we are using
MODEL_ID = os.environ.get("MODEL_ID")
print(f"MODEL_ID: {MODEL_ID}")

completion = client.chat.completions.create(
    model=MODEL_ID,
    messages=[
        {
            "role" : "user",
            "content" : "In One Short paragraph, explain what a Large Language Model is to"
                        "10 year old"
        }
    ],
    max_tokens=200
)

print(completion.choices[0].message.content)

followup = client.chat.completions.create(
    model=MODEL_ID,
    messages=[
        {
            "role" : "user",
            "content" : "Can you explain again?"
        }
    ],
    max_tokens=200
)
print("without history model is confused\n")
print(followup.choices[0].message.content)

conversation = [
    {
         "role" : "user",
         "content" : "In One Short paragraph, explain what a Large Language Model is to"
                        "10 year old"
    },
    {
         "role": "assistant",
         "content": completion.choices[0].message.content

    },
    {
        "role": "user",
        "content": "Can you explain again?"
    }
]

followup_with_history = client.chat.completions.create(
    model=MODEL_ID,
    messages=conversation,
    max_tokens=200
)

print("with the full history model understands\n")

print(followup_with_history.choices[0].message.content)
