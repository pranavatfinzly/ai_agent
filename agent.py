"""A minimal banking agent: an LLM + tools + a loop."""

import json
import sys

import truststore
from dotenv import load_dotenv
from groq import APIError, Groq

from tools import (MOCK_DB, TOOL_REGISTRY, TOOL_SCHEMAS, check_transfer,
                   find_account)

MODEL = "openai/gpt-oss-20b"
MAX_STEPS = 5

# Who the user is. Set by identify_user(); until then no other tool
# may run, and money may only ever leave this account.
user_account = None

truststore.inject_into_ssl()  # trust the OS certificate store
load_dotenv()
# Reads GROQ_API_KEY from the environment. Fail fast on a network
# blip instead of waiting 60s x 3 attempts.
client = Groq(timeout=20, max_retries=1)

# The prompt only steers the model; it enforces nothing. The real
# safety checks are in code: check_guardrails() and ask_approval().
SYSTEM_PROMPT = """You are a helpful banking assistant.

Identifying the user:
- Before doing anything else, ask the user for their name.
- Call identify_user only with a name the user actually gave you.
  Only help once it succeeds.
- If it fails, say the name was not found and ask again.
- The account identify_user returns is the user's own account. Use it
  whenever the user says "my" or "mine".
- To get another person's account ID from their name, call find_account.

Rules:
- Always use the provided tools to get balances, transactions, or make
  transfers. Never guess or invent account data.
- If the user hasn't given an account ID you need, ask for it.
- Before any transfer, state the amount and the accounts involved.
- Keep answers short and clear
- Always use a tool to look up balances and transactions.
- Never invent account numbers, balances, or amounts.
- If a tool returns an error, explain it to the user plainly.
- If a transfer is declined, confirm it was cancelled.
- Reply in plain ASCII text. No markdown, tables, or emoji.
- Keep answers short.

How access works:
- The user can only view the balance and transactions of their own
  account.
- Money can only be sent from the user's own account.
- The app checks every transfer, then asks the user to approve it.
  You cannot skip or override these checks.
"""

IDENTIFY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "identify_user",
        "description": "Identify who the user is from their name. "
                       "Must succeed before any other tool can be used.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The user's name"},
            },
            "required": ["name"],
        },
    },
}
ALL_SCHEMAS = TOOL_SCHEMAS + [IDENTIFY_SCHEMA]


def identify_user(name):
    """Remember who the user is. Can only be set once per session."""
    global user_account
    if user_account is not None:
        owner = MOCK_DB[user_account]["owner"]
        return {"error": f"Already identified as {owner}."}
    result = find_account(name)
    if "error" not in result:
        user_account = result["account_id"]
    return result


def check_guardrails(name, args):
    """Return an error dict if the tool call must be blocked, else None."""
    if name in ("get_balance", "get_transactions"):
        if args["account_id"] != user_account:
            return {"error": f"You can only view your own account, "
                             f"{user_account}."}
    if name == "transfer_money":
        if args["from_account"] != user_account:
            return {"error": f"You can only send money from your own "
                             f"account, {user_account}."}
        return check_transfer(**args)
    return None


def ask_approval(args):
    # Show owner names too, so a wrong account number is easy to spot.
    from_owner = MOCK_DB[args["from_account"]]["owner"]
    to_owner = MOCK_DB[args["to_account"]]["owner"]
    print("\n  !! APPROVAL NEEDED !!")
    print(f"  Transfer ${args['amount']} "
          f"from {args['from_account']} ({from_owner}) "
          f"to {args['to_account']} ({to_owner})")
    answer = input("  Approve? (y/n): ")
    return answer.strip().lower() == "y"


def run_agent(messages):
    # messages is the whole conversation so far, shared across turns.
    # Everything we append here is remembered next turn too.

    # The agent loop. Cap it so a confused model can't loop forever.
    for step in range(1, MAX_STEPS + 1):
        print(f"\n[STEP {step}] Asking the model...")

        # 1. Call the model with the conversation AND the tool menu.
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=ALL_SCHEMAS,
        )
        message = response.choices[0].message

        # 2. No tool calls? The model is done. Remember its answer
        #    so the next turn can build on it, then return it.
        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content or ""})
            return message.content

        # 3. The model wants tools. Save its request to the history,
        #    so on the next turn it remembers what it asked for.
        tool_calls = [call.model_dump() for call in message.tool_calls]
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": tool_calls,
        })

        # 4. Run each tool the model asked for.
        for call in message.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            print(f"  TOOL CALL: {name}")
            print(f"  ARGS:      {args}")

            # 5. Guardrails: nothing runs until the user is identified,
            #    and users may only touch their own account. Invalid
            #    transfers are blocked before bothering the human, then
            #    a human must approve any money movement.
            if name == "identify_user":
                result = identify_user(**args)
            elif user_account is None:
                result = {"error": "User not identified. Ask for their "
                                   "name and call identify_user first."}
            else:
                error = check_guardrails(name, args)
                if (error is None and name == "transfer_money"
                        and not ask_approval(args)):
                    error = {"error": "User declined. Transfer cancelled."}
                result = error or TOOL_REGISTRY[name](**args)
            print(f"  RESULT:    {result}")

            # 6. Send the result back, tagged with the call's id.
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

        # 7. Loop again: the model now sees the tool results.

    return "Sorry, I couldn't finish that in time."


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # safe on any console
    print("Banking agent ready. Type 'quit' to exit.")

    # Memory: one message list for the whole chat, not one per turn.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("quit", "exit"):
            break
        messages.append({"role": "user", "content": user_input})
        try:
            answer = run_agent(messages)
        except APIError as error:
            answer = f"(API problem: {error}. Try again.)"
        print(f"\nAgent: {answer}")
