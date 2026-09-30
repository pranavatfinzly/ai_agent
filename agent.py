"""A minimal banking agent: an LLM + tools + a loop."""

import json
import sys

import truststore
from dotenv import load_dotenv
from groq import APIError, Groq

from tools import TOOL_REGISTRY, TOOL_SCHEMAS

MODEL = "openai/gpt-oss-120b"
MAX_STEPS = 5

truststore.inject_into_ssl()  # trust the OS certificate store
load_dotenv()
client = Groq()  # reads GROQ_API_KEY from the environment

SYSTEM_PROMPT = """You are a helpful banking assistant.
The user is Alice. Her account is ACC-1001.
Her friend Bob has account ACC-2002.

Rules:
- Always use a tool to look up balances and transactions.
- Never invent account numbers, balances, or amounts.
- If a tool returns an error, explain it to the user plainly.
- If the user rejects a transfer, confirm it was cancelled.
- Reply in plain ASCII text. No markdown, tables, or emoji.
- Keep answers short."""


def ask_approval(args):
    print("\n  !! APPROVAL NEEDED !!")
    print(f"  Transfer ${args['amount']} "
          f"from {args['from_account']} to {args['to_account']}")
    answer = input("  Approve? (y/n): ")
    return answer.strip().lower() == "y"


def run_agent(user_message):
    # The conversation so far: instructions + what the user asked.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

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

        # 2. No tool calls? The model is done. Return its answer.
        if not message.tool_calls:
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

            # 5. Guardrail: a human must approve any money movement.
            if name == "transfer_money" and not ask_approval(args):
                result = {"error": "User declined. Transfer cancelled."}
            else:
                result = TOOL_REGISTRY[name](**args)
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
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("quit", "exit"):
            break
        try:
            answer = run_agent(user_input)
        except APIError as error:
            answer = f"(API problem: {error}. Try again.)"
        print(f"\nAgent: {answer}")
