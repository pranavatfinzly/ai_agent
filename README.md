# Minimal Banking Agent

An LLM agent in about 25 lines of loop code: the model picks tools,
our code runs them, and a human approves any money transfer.

| File | Purpose |
|------|---------|
| `tools.py` | Mock bank data, three tools, and their JSON schemas |
| `agent.py` | The agent: loop, guardrails, approval prompt, chat memory |

## Setup

```
pip install -r requirements.txt
cp .env.example .env        # then paste your key from console.groq.com
python agent.py
```

Type `quit` or `exit` to leave. To change the model, edit `MODEL`
at the top of `agent.py` (default `openai/gpt-oss-20b`).

## How it works

- **Tools**: `get_balance`, `get_transactions`, `transfer_money`,
  backed by an in-memory mock DB (resets every run).
- **Loop**: each turn calls the model with the tool schemas, runs any
  tool calls, feeds results back, and repeats until the model answers
  in plain text. Capped at `MAX_STEPS = 5` per turn.
- **Memory**: one message list is kept for the whole chat, so
  follow-ups like "send him another $20" work across turns.
- **Guardrails**: transfers are checked in code before a human sees
  them. Money may only leave `ACC-1001`; unknown accounts, same-account
  transfers, non-positive amounts, and insufficient funds are blocked.
- **Human approval**: every valid transfer shows the amount and both
  owners' names and waits for `y/n`.

## Mock accounts

| Account | Owner | Starting balance |
|---------|-------|------------------|
| `ACC-1001` | Pranav (the user) | $5,250.00 |
| `ACC-2002` | Bob | $820.50 |
| `ACC-3003` | Charlie | $1,340.75 |

## Try it

```
What's my balance?
Show my last 3 transactions.
Send Bob $50.
Send him another $20.
Move $100 from Charlie's account to mine.   # blocked by guardrail
```

## If the API fails on stage

- **401 / auth error**: check that `.env` exists in this folder and
  contains `GROQ_API_KEY=...`.
- **429 / rate limit**: wait 30 seconds and retry. Keep a second
  Groq key in your notes and swap it into `.env`.
- **Model not found / deprecated**: set `MODEL` to another tool-calling
  model listed at console.groq.com/docs/models
  (e.g. `openai/gpt-oss-120b`).
- **SSL / certificate error** (corporate networks like Zscaler):
  `truststore` in `agent.py` already handles this by using the
  Windows certificate store. Make sure `pip install -r
  requirements.txt` was run so `truststore` is installed.
- **"Request timed out"**: a network blip. The agent prints one line
  and keeps running, so just retype the prompt. A phone hotspot
  avoids the corporate proxy entirely.
- **No internet**: switch to a pre-recorded terminal run of
  `agent.py` and narrate over it. Record one the day before.
