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
    # TODO (approval gate):
    #   a. Print the transfer details (amount, from, to)
    #   b. Ask "Approve? (y/n)" with input()
    #   c. Return True only if the answer is "y"
    pass


def run_agent(user_message):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for step in range(1, MAX_STEPS + 1):
        print(f"\n[STEP {step}] Asking the model...")

        # 1. Call the model with messages + TOOL_SCHEMAS

        # 2. If there are no tool calls, return the text answer

        # 3. Append the model's tool-call request to messages

        # 4. For each tool call: read its name and JSON args, print them

        # 5. If it's transfer_money, ask_approval() first;
        #    if rejected, the result is an error message instead

        # 6. Run the tool, print the result, append it as a
        #    "tool" message with the matching tool_call_id

        # 7. Loop again so the model can see the results

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
