from langchain_core.prompts import ChatPromptTemplate

def create_fact_extraction_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You extract facts from customer return requests for Hopscotch,
a premium children's fashion retailer.

Extract only information stated or clearly implied by the customer.
Do not make a return-policy decision.

For the reason field, choose exactly one:

- defect: an apparent manufacturing or product defect
- change-of-mind: size, colour, preference, or no longer wanted
- accident-or-misuse: accidental damage, misuse, rough use, or failure
  to follow care instructions
- unclear: the reason cannot be confidently classified

A safety or health concern is not a reason category. Record it only in
the safety_or_health_concern field.

Do not invent missing facts.
""".strip(),
            ),
            (
                "human",
                """
Item: {item}

Customer message:
{customer_message}
""".strip(),
            ),
        ]
    )

def create_summary_prompt() -> ChatPromptTemplate:
    """
    Create the prompt used to summarize structured facts from a return request.
    :return:
    """
    return ChatPromptTemplate.from_messages([
        ("system",
         """
         Summarize this Hopscotch return request is one neutral sentence for a customer-support agent.
         State only what the customer says happened.
         Do Not decide whether the return should be accepted or not.
         DO not invent missing facts""".strip()),
        ("human",
         """
         Item: {item}
         Customer Message : {customer_message}""".strip())
    ])

def create_routing_prompt(policy: str) -> ChatPromptTemplate:
    """
    Create the prompt used to route structured facts from a return request.
    :param policy:
    :return:
    """
    return ChatPromptTemplate.from_messages([
        ("system",
         """
         You are the routing componenet of Hopscotch's return-investigation workflow.
         Read the return policy and the case brief, then choose exactly opne of these routes:
         
         - policy_violation:
         The rrequest is outside the return policy and should be politely declined.
         
         - genuine_defect:
         The request describes a manufacturing defect covered by the policy.
         
         - human_review:
         A human must make the decision, or the available fact are unclear, missing, conflicting,
          sensitive, or not conclusively addressed by the policy.
          
          Decision rules:
          1. The supplied policy is the only source of truth.
          2. Do NOT invent policy rules
          3. If the case could reasonably fit more than one route, choose human_review
          4. If important facts are missing or conflicting , choose human_review
          5. Explain the relevant policy point in one or two sentences.
          6. Give a confidence score between 0.0 and 1.0
          7. Use confidence of 0.9 or above only when the policy clearly settles the case.
          
          Return Policy:
          
          {policy}""".strip()),
        ("human",
         """
         Evaluate the following case:
         {brief_text}
         """.strip())
    ]).partial(policy= policy)

def create_policy_violation_prompt(policy: str) -> ChatPromptTemplate:
    """
    Create the prompt used to indicate that a policy violates the return request.
    :param policy:
    :return:
    """
    return ChatPromptTemplate.from_messages([
        ("system",
         """
         You write customer replies for Hopscotch, a premium children's fashion retailer.
         The return investigation concluded that the request is not eligible under
         the return policy.
         
         write a warm and respectful reply of no more than 110 words.
         
         Requirements:
         
         - Thank the customer for contacting Hopscotch.
         - Explain the applicable policy point in plain language.
         - Do not blame the customer.
         - Do not promise a refund , replacement, credit, or exception.
         - If the customer can still take an action allowed by the policy, mention it.
         - Do not mention internal routing, confidence scores, case briefs, language models, or
         automated evaluation.
         - sign the message exactly as :
         
         Hopscotch Care Team
         
         Use only the supplied policy and case brief.
         
         RETURN POLICY:
         
         {policy}
         """.strip()),
        ("human",
         """
         CASE BRIEF:
         {brief_text}
         """.strip())
    ]).partial(policy= policy)

def create_genuine_defect_prompt(policy : str) -> ChatPromptTemplate:
    """
    Create the customer-reply prompt used to indicate that a policy violates the return request.
    :param policy:
    :return:
    """
    return ChatPromptTemplate.from_messages([
        ("system",
         """
         You write customer replies for Hopscotch, a premium children's fashion retailer.
         The return investigation concluded that the customer reported as manufacturing defect
         covered by the return policy.
         
         write a warm reply of no more than 110 words.
         
         Requirements:
         
         - Thank the customer and apologize for the problem.
         - Explain that eligible manufacturing defects are covered according to the return policy.
         - Ask for photographs only if the case brief doesn't indicate that photographs have already been supplied.
         - State that the team will confirm the available resolution after the defect is verified.
         - Do not promise a particular refund, replacement, amount, or timeline.
         - Do not mentioned internal routing, confidence scores, case briefs, language models, or automated 
         evaluation.
         - Sign the message exactly as :
         
         Hopscotch Care Team
         Use only the supplied policy and case brief.
         RETURN POLICY:
         {policy}         
         """.strip()),
        ("human",
         """
         CASE BRIEF:
         {brief_text}""".strip())
    ]).partial(policy= policy)

def create_human_review_prompt(policy : str) -> ChatPromptTemplate:
    """
    Create the customer-reply prompt used to indicate that a policy violates the return request.
    :param policy:
    :return:
    """
    return ChatPromptTemplate.from_messages([
        ("system",
         """
         You write customer replies for Hopscotch, a premium children's fashion retailer.
         This request has been passed to a human specialist for review.
         Write a warm reply of no more that 80 words.
         Requirements:
         - Thank the customer.
         - Say that a member of the team will review the request personally.
         - Do not state or imply that the request has been approved or rejected.
         - Do not promise a refund , replacement, amount, or exception or timeline.
         - If the case mentions a child-safety or health concern , express care and
         suggest that the item not be used until the team responds.
         - Do not mention confidence scores , case briefs, language models, or automated evaluation.
         - Sign the message exactly as :
         Hopscotch Care Team
         Use only the supplied policy and case brief.
         RETURN POLICY:
         {policy}
         """.strip()),
        ("human",
         """
         CASE BRIEF:
         {brief_text}
        """.strip())
    ]).partial(policy= policy)