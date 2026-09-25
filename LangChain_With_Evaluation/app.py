# import os
# import time
# from functools import partial
# from logging import exception
#
# import pandas as pd
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough, RunnableBranch
# import json
# from typing import Literal, Optional
# from pydantic import BaseModel, Field , ValidationError, field_validator
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
#
# load_dotenv()
#
# llm = ChatOpenAI(
#     model= os.getenv("OPENAI_MODEL"),
#     openai_api_key = os.getenv("OPENROUTER_API_KEY"),
#     temperature=float(os.getenv("OPENROUTER_TEMPERATURE"))
# )
#
# print("LLM Configured: " ,llm.model_name)
#
# #/Users/manasisuthar/FDE
#
# returns_df = pd.read_csv("/Users/manasisuthar/FDE/hopscotch_returns.csv")
#
# with open("/Users/manasisuthar/FDE/hopscotch_return_policy.txt","r") as f:
#     POLICY = f.read()
#
# print(POLICY)
#
# pd.set_option('display.max_colwidth', 90)
# returns_df.head(6)
#
# cases = returns_df[["customer_message", "item", "order_value_inr", "days_since_delivery"]].to_dict("records")
#
# print(cases)
#
# true_routes = returns_df["true_route"].tolist()
#
# print("Number of true routes: ", len(true_routes))
# print("NUmber of cases: ", len(cases))
# print(cases[1])
#
# def input_gate(req:dict) -> dict:
#     """Reject requests we cannot investigate, BEFORE any LLM call."""
#     message = req["customer_message"]
#
#     if not isinstance(message, str) or len(message.strip()) < 15:
#         raise ValueError("Input gate: the customer message is missing or too short to investigate")
#     if len(message) > 1500:
#         raise ValueError("Input gate: the customer message is too long to investigate")
#
#     for key in ('item' , 'order_value_inr', 'days_since_delivery'):
#         if req.get(key) is None:
#             raise ValueError("Input gate: the %s is missing or too short to investigate" % key)
#
#     return req
#
# input_gate_step = RunnableLambda(input_gate)
#
# print("Good Request -> " , input_gate_step.invoke(cases[1])["item"])
#
# try:
#     input_gate_step.invoke({"customer_message": "Hello World",
#                             "order_value_inr": 123,
#                             "days_since_delivery": 456,
#                             "item":"Raincoat"})
# except ValueError as e:
#     print("Bad Request: " ,e)
#
#
# class CaseFacts(BaseModel):
#     """The Four facts we extract from a customer's return message"""
#
#     problem : str = Field(description="A short phrase (max 8 words) describing what went wrong")
#
#     reason: Literal["defect","change_of_mind", "accident_or_misuse","unclear"] = Field(
#         description="Why Customer wants to return the item."
#     )
#
#     used_or_worn: Literal["yes", "no","unknown"] = Field(
#         description="Yes if the customer says item was worn, used or washed. No if they say it unworn; otherwise unknown"
#     )
#
#     safety_or_health_concern: Literal["yes","no"] = Field(
#         description="Yes if the message mentions a child safety risk, injury skin reaction or "
#                     "allergy; otherwise no"
#     )
#
# facts_parser = PydanticOutputParser(pydantic_object=CaseFacts)
#
# print(facts_parser.get_format_instructions())
# print("-"*60)
#
# good_json = '{"problem" : "zip broke", "reason" : "defect", "used_or_worn": "yes", "safety_or_health_concern": "no"}'
# print("Parsed Reply: " , facts_parser.parse(good_json))
#
# bad_json = '{"problem":"zip broke","reason": "Defect", "used_or_worn":"yes", "saftey_or_health_concern":"no"}'
# try:
#     facts_parser.parse(bad_json)
# except Exception as e:
#     print("Exception: ", e)
#
# extract_prompt = ChatPromptTemplate.from_messages([
#     ("system",
#      "You extract facts from a customer's return request for hopscotch . a kids fashion retailer.\n"
#      "{format_instructions}\n"
#      "Return only the JSON object, with no commentary."),
#     ("human","Item : {item} \n Customer message : {customer_message}"),
# ]).partial(format_instructions=facts_parser.get_format_instructions())
#
# extract_chain = (extract_prompt
#                  | llm
#                  | facts_parser
#                  | RunnableLambda(lambda x: x.model_dump()))
#
# print()
# print("R02 (School shoes): ", extract_chain.invoke(cases[1]))
# print("R05 (leggings ): ", extract_chain.invoke(cases[4]))
#
# summary_prompt = ChatPromptTemplate.from_messages([
#     ("system",
#      "Summerise this Hopscotch return in ONE neutral sentence for a support agent."
#      "State what the customer says happened. Do not decide whether the return is allowed."),
#     ("human","Item : {item} \n Customer message : {customer_message}"),
# ])
#
# summary_chain = summary_prompt | llm | StrOutputParser()
#
# def compute_flags(req: dict) -> dict:
#     """Flags we can compute exactly from order data: no LLM needed, so we don't use one"""
#
#     return {
#         "within_30_days" : req["days_since_delivery"] <= 30,
#         "within_90_days" : req["days_since_delivery"] <=90,
#         "high_value" : req["order_value_inr"] > 5000,
#     }
#
# print(compute_flags(cases[1]))
#
# gather = RunnableParallel(
#     facts = extract_chain,
#     summary = summary_chain,
#     flags = RunnableLambda(compute_flags),
#     requests = RunnablePassthrough()
# )
#
# def build_brief(state: dict) -> dict:
#     """Turn the gathered pieces into one case brief (plain text) the router can read."""
#     req, facts, flags = state["requests"], state["facts"], state["flags"]
#     yes_no = lambda flag: "yes" if flag else "no"
#     brief_text = (
#         "CASE BRIEF\n"
#         f"Item: {req['item']}\n (INR {req['order_value_inr']:,}), delivered {req['days_since_delivery']} days ago\n"
#         f"Within 30-day window: {yes_no(flags['within_30_days'])} |"
#         f"Within 90-day window: {yes_no(flags['within_90_days'])} |"
#         f"High value (over INR 5000): {yes_no(flags['high_value'])}\n"
#         f"Customer reason: {facts['reason']} | Used or worn: {facts['used_or_worn']} | "
#         f"Safety or health concern: {facts['safety_or_health_concern']}\n"
#         f"Problem: {facts['problem']}\n"
#         f"Summary: {state['summary']}\n"
#         f"Customer message: {req['customer_message']}\n"
#     )
#
#     return {**state, "brief_text": brief_text}
#
# intake_chain = RunnableLambda(input_gate) | gather | RunnableLambda(build_brief)
#
# result = intake_chain.invoke(cases[3])
#
# print(result)
#
# briefs = intake_chain.batch(cases, config={"max_concurrency": 3}, return_exceptions=True)
#
#
#
# class RouteDecision(BaseModel):
#     """The router's decision about one return case"""
#
#     reason: str = Field(
#         description="One or two sentences explaining the decision, citing the relevant policy point."
#     )
#
#     route: Literal["policy_violation", "genuine_defect", "human_review"] = Field(
#         description="The single route this case should take"
#     )
#
#     confidence: float = Field(
#         ge=0.0, le=1.0,
#         description="How sure you are , fro 0.0 to 1.0. Use 0.9 or more only when the policy clearly settles the case."
#     )
#
# router_llm = llm.with_structured_output(RouteDecision, method="function_calling")
#
# router_prompt =  ChatPromptTemplate.from_messages([
#     ("system",
#      "You are the routing step of Hopscotch's return-investigation workflow."
#      "Read the policy and the case brief, then choose exactly one route. \n\n"
#      "route: \n"
#      "- policy_violation: the request is outside the return policy and should be politely declined.\n"
#      "- genuine_defect: a manufacturing defect covered by the policy.\n"
#      "- human_review: any case the policy says a human must decide, or any case where the facts are unclear"
#      ", missing or conflicting \n"
#      "Rules: \n"
#      "-The policy is the only source of truth.\n"
#      "-When you are torn between two routes, choose human_review and say so in your reason.\n"
#      "- Be honest about your confidence.\n"
#      "POLICY : \n{policy}"),
#      ("human","{brief_text}")
# ]).partial(policy=POLICY)
#
# def decision_to_dict(decision: RouteDecision) -> dict:
#     """Pydantic object -> plain dict, so it flows through the rest of our pipeline easily."""
#     return  decision.model_dump()
#
# router_chain = router_prompt | router_llm | RunnableLambda(decision_to_dict)
#
# print("RO4 (zip brok, 40 days): ")
# print(router_chain.invoke(briefs[4]))
#
# CUSTOMER_REPLY_HUMAN = "POLICY:\n{policy}\n\n{brief_text}"
#
# policy_violation_prompt = ChatPromptTemplate.from_messages([
#     ("system",
#      "You write customer replies for hopscotch , a premium kids' fashion retailer"
#      "The return investigation has concluded that this request is NOT eligible under our policy.\n"
#      "Write a short, warm, respectful reply (under 110 words) that thanks the customer, explain which policy point applies"
#      "in plain language, does not blame cusotmer, and does NOT promise refund, a replacement or an exception."
#      "If there is something the customer can still do within the policy , mention it\n"
#      "Sign off as 'Hopscotch Care Team"),
#     ("human", CUSTOMER_REPLY_HUMAN)
# ]).partial(policy=POLICY)
#
# genuine_defect_prompt = ChatPromptTemplate.from_messages([
#     ("system",
#     "You write customer replies for Hopscotch, a premium kid's fashion retailer."
#     "The return investigation has concluded that this is a manufacturing defect covered by our policy.\n"
#     "Write a short, warm reply (under 110 words) thet apologises, confirms that defects are covered for up to 90 days"
#     "from delivery, ask for photos ONLY if the customer has not already mentioend attaching any , and says our team will"
#     "confirm replacement or refund once the defect is verified. DO NOT promise specific timeline or amounts\n"
#     "Sign off as 'Hopscotch Care Team'"),
#     ("human", CUSTOMER_REPLY_HUMAN)
# ]).partial(policy=POLICY)
#
# human_review_prompt = ChatPromptTemplate.from_messages([
#     ("system",
#      "You write customer replies for Hopscotch , a premium kids' fashion retailer"
#      "Thus request has been passed to a human specialist for review.\n"
#      "Write a short, warm reply (under 80 words) that thanks the customer and says a member of our team will review the"
#      "request personally. Do NOT state or hint at any decision (neither approval nor refusal.)"
#      "If the brief mentions a child-safety or health concern , express care and suggest the item not used until"
#      "we have been in touch.\n"
#      "Sign off as 'Hopscotch Care Team'"
#      ),
#     ("human", CUSTOMER_REPLY_HUMAN)
# ]).partial(policy=POLICY)
#
# policy_violation_chain = policy_violation_prompt | llm | StrOutputParser()
# genuine_defect_chain = genuine_defect_prompt | llm | StrOutputParser()
# human_review_chain = human_review_prompt | llm | StrOutputParser()
#
# print(" Branch chains ready.")
#
# branch = RunnableBranch(
#     (lambda state: state["route"] == "policy_violation",policy_violation_chain),
#     (lambda state: state["route"] == "genuine_defect",genuine_defect_chain),
#     human_review_chain
# )
#
# test_brief = briefs[1]["brief_text"]
#
# for route in ["genuine_defect" "policy_violation", "banana"]:
#     print(f"------route = {route!r} ----")
#     print(branch.invoke({"route": route,"brief_text": test_brief}))
#     print()
#
#
# def flatten(state: dict) -> dict:
#     """Pick the fields the branch (and our later checks) need out of the pipeline state."""
#     decision = state["decision"]                  # the router's answer (added by .assign below)
#     return {
#         "customer_message": state["requests"]["customer_message"],
#         "brief_text": state["brief_text"],
#         "route": decision["route"],               # the branch reads this key to choose a path
#         "confidence": decision["confidence"],
#         "reason": decision["reason"],
#     }
#
#
# return_pipeline = (
#     intake_chain                                          # chain: gate -> parallel intake -> brief
#     | RunnablePassthrough.assign(decision=router_chain)   # router: classify, and add the result under "decision"
#     | RunnableLambda(flatten)                             # tidy the state into the small dict the branch needs
#     | RunnablePassthrough.assign(reply=branch)            # branch: dispatch by route, and add the result under "reply"
# )
#
#
# def show(result: dict) -> None:
#     """Print a pipeline result in a readable way"""
#
#     print(f"ROute: { result['route']}  (confidence: {result['confidence']})")
#     print(f"Why: { result['reason']}")
#     print(f"\n CUSTOMER MESSAGE : { result['customer_message']}")
#     print(f"\n reply : { result['reply']}")
#     print("-" * 70)
#
#
# for index in [13, 1, 8]:
#     show(return_pipeline.invoke(cases[index]))
#
#
# def predict_all(chain, briefs_list, escalate_failure=False):
#     """Run 'chain over every saved brief. Requests that failed earlier (or fail here) are kept,
#     not dropped"""
#     failure_route = "human_review" if escalate_failure else None
#
#     ok = [i for i, b in enumerate(briefs_list) if not isinstance(b, Exception)]
#     outputs = chain.batch([briefs_list[i] for i in ok], config = {"max_concurrency": 5}, return_exceptions = True)
#
#     results = [
#         {
#             "route" : failure_route or "intake_error", "confidence" : None, "reason" : "intake gate stopped this request"
#         }
#         for _ in  briefs_list
#
#     ]
#
#     for i, out in zip(ok, outputs):
#         results[i] = out if isinstance(out, dict) else {
#             "route" : failure_route or "route_error", "confidence" : None, "reason" : str(out)
#
#         }
#
#     return results
#
# def summarise(name, true, results):
#     """One scoreboard row: accuracy plus the four kinds of cost"""
#
#     n = len(true)
#     pred = [r["route"] for r in results]
#     pairs = list(zip(true, pred))
#     return {
#         "system": name,
#         "accuracy": round(sum(t == p for t, p in pairs) / n ,2),
#         "safety_misses": sum(t == "human_review" and p != "human_review" for t, p in pairs),
#         "wrongful_denials" : sum(t == "genuine_defect" and p == "policy_violation" for t, p in pairs),
#         "wrongful_approvals" : sum(t == "policy_violation" and p == "genuine_defect" for t, p in pairs),
#         "over_escalations": sum(t != "human_review" and p == "human_review" for t, p in pairs)
#     }
#
# baseline = predict_all(router_chain, briefs)
#
# scoreboard = [summarise("Router alone", true_routes, baseline)]
# pd.DataFrame(scoreboard).to_csv("scoreboard.csv")
#
# pd.crosstab(pd.Series(true_routes, name = "true routes"), pd.Series([r["route"] for r in baseline], name = "router said"))
#
#
# def apply_threshold(results, threshold):
#     """Escalate anything the router was not confident about (or that failed outright)."""
#
#     out = []
#     for r in results:
#         if r["confidence"] is None or r["confidence"] < threshold:
#             out.append({**r , "route" : "human_review",
#                         "reason" : f"escalated: confidence {r['confidence']} is below {threshold}"})
#         else:
#             out.append(r)
#     return out
#
# sweep_rows = []
# for threshold in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
#     adjusted = apply_threshold(baseline, threshold)
#     row = summarise(f"threshold {threshold}", true_routes, adjusted)
#     row["threshold"] = threshold
#     row["escalated_total"] = sum(r["route"]  == "human_review" for r in adjusted)
#     sweep_rows.append(row)
#
# sweep = pd.DataFrame(sweep_rows).set_index("threshold").drop(columns=["system"])
# print(sweep)