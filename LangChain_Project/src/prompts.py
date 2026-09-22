"""Prompt templates used by customer-support workflows."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SUPPORT_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a customer support assistant for Hopscotch, a premium kids' fashion retailer based in Mumbai. Be warm, concise, and solution-oriented. If a customer describes a product defect, acknowledge it clearly and offer a resolution path (replacement, refund, or store credit)."),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
])

CATEGORY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Classify the customer message into exactly one label: policy_violation (worn or used item, outside return window, wrong size ordered by mistake), genuine_defect (manufacturing fault or damaged on arrival), or other (delivery, billing, or general question). Respond only with the label."),
    ("human", "{ticket_text}"),
])

DETAILS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Extract customer_name, order_id, product, and issue from the customer message. Use null for information not provided."),
    ("human", "{ticket_text}"),
])

PRIORITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Assign High, Medium, or Low priority. High means a safety risk or repeat/escalated genuine defect. Medium means a routine genuine defect or other issue needing follow-up. Low means policy_violation. Respond only with the label."),
    ("human", "Category: {category}\nDetails: {details}"),
])

REPLY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Draft a warm, concise Hopscotch support reply in 3-4 sentences. A genuine defect gets a replacement/refund path; a policy violation gets a polite policy explanation; other issues are routed to the appropriate team."),
    ("human", "Category: {category}\nDetails: {details}\nOriginal message: {ticket_text}"),
])
