from random import sample

import tiktoken
import re

USING_REAL_TOKENISER = False
try:
    ENC = tiktoken.get_encoding("o200k_base")
    USING_REAL_TOKENISER = True
except Exception as e:
    ENC = None
    print("Could not load tokeniser vocabulary:", type(e).__name__)
    print("Falling back to rough character based Estimate")

def _fallback_pieces(text):
    """Crude stand in for BPE: Split on words and punctiation , chop long runs"""
    out = []
    for piece in re.findall(r"\s*\w+|\s[^\w\s]|\s+", text):
        while len(piece) > 4:
            out.append(piece[:4])
            piece = piece[4:]
        if piece:
            out.append(piece)
    return out

def tokenize(text):
    """Tokenize text into a list of tokens"""
    if USING_REAL_TOKENISER:
        return [ENC.decode_single_token_bytes(t).decode("utf-8", errors= "replace")
                for t in ENC.encode(text)]
    return _fallback_pieces(text)

def count_tokens(text):
    """Count the number of tokens in a text"""
    if USING_REAL_TOKENISER:
        return len(ENC.encode(text))
    return len(_fallback_pieces(text))

print("Real BPE tokeniser active:", USING_REAL_TOKENISER)
sample = "My broadband has been down since Tuesday evening."
print("Sample:", sample)
print("split into: ", tokenize(sample))
print("That is : ", count_tokens(sample), "tokens for ", len(sample) ,"characters" )

print()

# Snapshot pricing , August 2026. Verify against official pricing pages before relying on this.

PRICING = {
   #model :     (input $/1M Ouput $/1M Context window)
    "GPT-5.5" :          (5.00, 30.00, 400_000),
    "Claude Opus 5":     (5.00, 25.00, 1_000_000),
    "Claude Sonnet 5":   (2.00, 10.00, 1_000_000),
    "Claude Haiku 4.5":  (1.00, 5.00, 200_000),
    "Gemini 3.1 pro" :    (2.00, 12.00, 1_000_00),
    "Llama 4 Scout (hosted)": (0.08, 0.30, 10_000_000),
    "DeepSeek V4 Flash" : (0.14, 0.28, 1_000_000)
}

def cost(model, input_tokens, output_tokens):
    """Cost in USD of One call to 'mode' with these tokens counts"""
    in_price, out_price, _window = PRICING[model]
    return (input_tokens* in_price + output_tokens*out_price)/1_000_000

def window(model):
    """The context window of 'model' , in tokens."""
    return PRICING[model][2]

print("100 inout tokens ans 200 output tokens on claude sonnet 5 costs" 
      f"${cost('Claude Sonnet 5', 100, 200):.6f}")

print()

SYSTEM_PROMPT = """You are the triage assistant for SpeedNet Broadband support.
Read the customer ticket and return the correct priority (P1, P2 or P3), the
correct category (outage, billing, speed, installation or other), and a one
line acknowledgement written for the customer. Be concise and never promise a
specific engineer visit time."""

TICKET = """Subject: No internet since Tuesday, third complaint

My connection has been completely dead since Tuesday evening. This is the third
time I am writing about it. Reference numbers SN-88214 and SN-88377. Nobody has
visited and nobody has called back. I work from home and I have already lost
two days of work. Please either fix this today or tell me how to close the
account."""

REPLY = """Priority: P1
Category: outage
Acknowledgement: We are sorry for the repeated delay on this. Your connection
issue is now marked urgent and our field team is being assigned today."""

print("The ticket as the model actually sees it, first 48 tokens: \n")
print(" | ".join(tokenize(TICKET)[:48]))
print("\n")

system_tokens = count_tokens(SYSTEM_PROMPT)
ticket_tokens = count_tokens(TICKET)
in_tokens = system_tokens + ticket_tokens
out_tokens = count_tokens(REPLY)

print(f"System prompt: {system_tokens:>5} tokens (you pay this on every call)")
print(f"Ticket text   : {ticket_tokens:>5} tokens  ({len(TICKET)} characters)")
print(f"Input total   : {in_tokens:>5} tokens")
print(f"Reply         : {out_tokens:>5} tokens  (billed at the higher output rate)")
print()

print(f"{'Model':<24}{'$ per ticket':>16}{'$ per 1,000 tickets':>22}")

for model in PRICING:
    one = cost(model, in_tokens, out_tokens)
    print(f"{model:<24}{one:>16.6f}{one * 1000:>22.2f}")

print()

VARIANTS = {
    "English":
        "My internet connection has been dead since Tuesday evening and nobody "
        "from SpeedNet has visited or called me back about it.",

    "Hindi (Devanagari)":
        "मेरा इंटरनेट कनेक्शन मंगलवार शाम से बंद है और स्पीडनेट से कोई भी "
        "व्यक्ति न आया है और न ही किसी ने वापस फोन किया है।",

    "Hinglish (Roman script)":
        "Mera internet connection mangalwar shaam se band hai aur SpeedNet se "
        "koi bhi aaya nahi hai aur na hi kisi ne wapas phone kiya hai.",

    "JSON payload":
        '{"ticket_id": "SN-88214", "channel": "web", "customer_tier": "gold", '
        '"body": "My internet connection has been dead since Tuesday evening '
        'and nobody from SpeedNet has visited or called me back about it."}',
}

MODEL = "Claude Sonnet 5"

print(f"{'Version':<26}{'Chars':>8}{'Tokens':>8}{'Chars/token':>14}"
      f"{'$ / 1,000 in':>14}")

for label, text in VARIANTS.items():
    tokens = count_tokens(text)
    chars_per_token = len(text)/tokens
    thousand = cost(MODEL, tokens, 0) *1000
    print(f"{label:<26}{len(text):>8}{tokens:>8}{chars_per_token:>14.2}{thousand:>14.3f}")

print("\nSame complaint. Same meaning. Different bill.")
print("First 30 tokens of the Hindi version:")
print(" | ".join(tokenize(VARIANTS["Hindi (Devanagari)"])[:30]))

print()


def bar(fraction, width=30):
    """Draw a text bar showing how full something is."""
    filled = int(round(min(fraction ,1.0) * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"

ticket_call_tokens = in_tokens + out_tokens
biggest = max(window(m) for m in PRICING)

print(f"One triage call = {ticket_call_tokens} tokens (prompt + ticket + reply)\n")
print(f"{'Model':<24}{'Window':>12}{'Tickets that fit':>20}   Window size, relative")

for model in PRICING:
    fits = window(model) // ticket_call_tokens
    print(f"{model:<24}{window(model):>12,}{fits:>20,}    {bar(window(model)/biggest)}")

TICKET_PER_WEEK = 1_250
week_tokens = ticket_call_tokens * TICKET_PER_WEEK // TICKET_PER_WEEK
print(f"\nOne Week of {TICKET_PER_WEEK:,} tickets = {week_tokens:,} tokens (prompt + ticket + reply)\n")
print(f"{'Model':<24}{'Weak as % of window':>21}     Fits in one call?")

for model in PRICING:
    used = week_tokens / window(model)
    verdict = "Yes" if used <= 1 else "No"
    print(f"{model:<24}{used * 100: 20.1f}%    {verdict:<4}   {bar(used)}")
print()

CUSTOMER_TURNS = [
    "My internet is not working since Tuesday evening.",
    "I already restarted the router twice, nothing changed.",
    "The lights on the router are red, not green.",
    "No, nobody called me back after my last complaint.",
    "I work from home, I cannot wait another two days for this.",
    "Can you at least tell me when the engineer will come?",
    "What compensation do I get for four days of downtime?",
    "Fine. Please confirm the visit slot in writing on email.",
]

BOT_REPLY = ("Thank you for confirming that. I have logged the detail against "
             "ticket SN-88214 and I am checking the outage status for your area "
             "right now. Please stay with me for a moment.")

MODEL = "Claude Sonnet 5"
reply_tokens = count_tokens(BOT_REPLY)

history = []
running_total = 0

first_input = None

print(f"{'Turn':<6}{'New msg':>9}{'Inout Sent:>12'}{'Running:>11'}{'vs turn 1:>12'}")

for turn , message in enumerate(CUSTOMER_TURNS, start=1):
    new_tokens = count_tokens(message)
    input_tokens = system_tokens + sum(history) + new_tokens
    if first_input is None:
        first_input = input_tokens
    turn_cost = cost(MODEL, input_tokens, reply_tokens)
    running_total += turn_cost
    print(f"{turn:<6}{new_tokens:>9}{input_tokens:>12}{turn_cost:>12.6f}"
          f"{running_total:>11.6f}{input_tokens / first_input:>11.1f}x")
    history.append(new_tokens)
    history.append(reply_tokens)

    typed =sum(count_tokens(m) for m in CUSTOMER_TURNS)
    print(f"\nThe customer typed {typed} tokens in total across all eight turns.")
    print(f"You paid to send {sum(history) + system_tokens * 8} input tokens.")
    print(f"Total for this one conversation on {MODEL}: ${running_total:.4f}")


print()


def simulate(mode, turns, keep_last=None, verbose=False, every =25):
    """Run a stateless chat for 'turns' turns. Optionally send only the last N messages."""
    history = []
    total = 0.0
    peak_input = 0
    broke_at = None
    cost_at_break = None

    if verbose:
        print(f"{'Turn':<7}{'Input Sent:>12'}{'Running $':>12}         Window used")


    for turn in range(1,turns + 1):
        message = CUSTOMER_TURNS[(turn - 1) % len(CUSTOMER_TURNS)]
        new_tokens = count_tokens(message)
        sent = history if keep_last is None else history[-keep_last:]
        input_tokens = system_tokens + sum(sent) + new_tokens

        if broke_at is None and input_tokens + reply_tokens > window(model):
            broke_at = turn
            cost_at_break = total
        total += cost(MODEL, input_tokens, reply_tokens)
        peak_input = max(peak_input, input_tokens)

        if verbose and  (turn % every == 0 or turn == 1):
            used = (input_tokens + reply_tokens) / window(model)
            flag = " OVER LIMIT" if input_tokens + reply_tokens > window(model) else ""
            print(f"{turn:<7}{input_tokens:>12}{total:>12.4f}        {bar(used)}{flag}")

        history.append(new_tokens)
        history.append(reply_tokens)

    return total, peak_input, broke_at, cost_at_break

STRESS_MODEL = "Claude Haiku 4.5"
print(f"400 turns on {STRESS_MODEL}, window {window(STRESS_MODEL):} tokens\n")
total, peak, broke_at, cost_at_break = simulate(STRESS_MODEL, 400, verbose=True)

print(f"\nPeak single request:  {peak:,} input tokens , which is "
      f"{peak/window(STRESS_MODEL)*100:.0f}% of the window.")

print(f"Total for 400 turns: ${total:.2f}, from a customer who typed "
      f"about 17 tokens a turn.")

if broke_at:
    print(f"First request that would be rejected: turn {broke_at}")


TURN_TOKENS = [count_tokens(message) for message in CUSTOMER_TURNS]

def turns_until_full(model,keep_last=None, cap=50_000):
    """How many turns until full turns are requested?"""
    history = []
    history_total = 0
    total = 0.0
    turn = 0
    while turn < cap:
        turn += 1
        new_tokens = TURN_TOKENS[(turn -1) % len(TURN_TOKENS)]
        sent_total = history_total if keep_last is None else sum(history[-keep_last:])
        input_tokens = system_tokens + sent_total + new_tokens
        if input_tokens + reply_tokens > window(model):
            return turn, total
        total += cost(model, input_tokens, reply_tokens)
        history.append(new_tokens)
        history.append(reply_tokens)
        history_total += new_tokens + reply_tokens

    return None, total

print("If the conversation never resets and history is never trimmed:\n")
print(f"{'Model':<24}{'Window':>12}{'Turns you get':>15}{'Spent by then':>16}")

for model in PRICING:
    turns, spend = turns_until_full(model)
    label = f"{turns:,}" if turns else "over 50,000"
    print(f"{model:<24}{window(model):>12,}{label:>15}{spend:>16.2f}")



print("\nRead the last two columns together. The model with the largest window "
      "lets you run the longest,")
print("and that is exactly why it can quietly run up the biggest bill before "
      "anything stops you.")

print(f"400 turns on {STRESS_MODEL}, three strategies\n")
print(f"{'Strategy':<26}{'Total $':>10}{'Peak input':>13}{'% of window':>14}{'Turns you get':>15}")

for label, keep in [("Send Everything", None),
                    ("Keep last 12 messages", 12),
                    ("Keep last 6 messages", 6)]:
    total, peak, _broke, _spend = simulate(STRESS_MODEL, 400, keep_last=keep)

    turns, _ = turns_until_full(STRESS_MODEL, keep_last=keep)
    reach = f"{turns:,}" if turns else "unlimited"
    used = peak / window(STRESS_MODEL) * 100
    print(f"{label:<26}{total:>10.2f}{peak:>13,}{used:>13.1f}%{reach:>15}")

    full, _, _, _ = simulate(STRESS_MODEL, 400)
    trimmed, _, _, _ = simulate(STRESS_MODEL, 400, keep_last=12)
    print(f"\nTrimming to the last 12 messages cuts this session's bill by "
          f"{(1 - trimmed / full) * 100:.0f}%.")
    print("It also means the model can no longer see turn 1, which is where the "
          "customer said the problem started on Tuesday.")


TICKET_PER_MONTH = 5_000
AVG_TICKET_PER_MONTH = 15

results = []
for model in PRICING:
    per_conversation, peek, broke_at, _ = simulate(model, TICKET_PER_MONTH)
    results.append((model, per_conversation, per_conversation*TICKET_PER_MONTH))

results.sort(key=lambda x: x[2])

print(f"{TICKET_PER_MONTH:,} tickets per month , {AVG_TICKET_PER_MONTH} turns each,"
      "full history resent every turn\n")
print(f"{'Model':<24}{'$/conversation':>18}{'$/month':>14}")

for model, per_conversation, monthly in results:
    print(f"{model:<24}{per_conversation:>18.4f}{monthly:>14,.2f}")

cheapest = results[0]
dearest = results[-1]
print(f"\nCheapest to most expensive: ${cheapest[2]:,.0f} against "
      f"${dearest[2]:,.0f} per month.")

# Routing: send the easy 80% to a cheap model, the hard 20% to a strong one
CHEAP, STRONG = "Claude Haiku 4.5", "Claude Opus 5"
cheap_conv, _, _, _ = simulate(CHEAP, AVG_TICKET_PER_MONTH)
strong_conv, _, _, _ = simulate(STRONG, AVG_TICKET_PER_MONTH)

all_strong = strong_conv * TICKET_PER_MONTH
routed = (cheap_conv * TICKET_PER_MONTH * 0.8) + (strong_conv * TICKET_PER_MONTH * 0.2)

print()
print(f"{'Everything on ' + STRONG:<48}${all_strong:>10,.2f} / month")
print(f"{'80% ' + CHEAP + ', 20% ' + STRONG:<48}${routed:>10,.2f} / month")
print(f"Routing saves {(1 - routed / all_strong) * 100:.0f}% of the bill.")


