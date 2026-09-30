"""A minimal banking agent: an LLM + tools + a loop."""

import json
import sys

import truststore
from dotenv import load_dotenv
from groq import APIError, Groq

from tools import MOCK_DB, TOOL_REGISTRY, TOOL_SCHEMAS, check_transfer

MODEL = "openai/gpt-oss-20b"
MAX_STEPS = 5
USER_ACCOUNT = "ACC-1001"  # money may only leave this account

truststore.inject_into_ssl()  # trust the OS certificate store
load_dotenv()
# Reads GROQ_API_KEY from the environment. Fail fast on a network
# blip instead of waiting 60s x 3 attempts.
client = Groq(timeout=20, max_retries=1)

SYSTEM_PROMPT = """You are a helpful banking assistant.
The user is Pranav, account ACC-1001.
Pranav's friend Bob has account ACC-2002.
Pranav's friend Charlie has account ACC-3003.

Rules:
- Always use a tool to look up balances and transactions.
- Never invent account numbers, balances, or amounts.
- If a tool returns an error, explain it to the user plainly.
- If the user rejects a transfer, confirm it was cancelled.
- Reply in plain ASCII text. No markdown, tables, or emoji.
- Keep answers short."""


def check_guardrails(args):
    """Return an error dict if the transfer must be blocked, else None."""
    if args["from_account"] != USER_ACCOUNT:
        return {"error": f"You can only send money from your own "
                         f"account, {USER_ACCOUNT}."}
    return check_transfer(**args)


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
            tools=TOOL_SCHEMAS,
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

            # 5. Guardrails: block invalid transfers before bothering
            #    the human, then a human must approve any money movement.
            error = None
            if name == "transfer_money":
                error = check_guardrails(args)
                if error is None and not ask_approval(args):
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
