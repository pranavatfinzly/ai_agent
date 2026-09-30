# Minimal Banking Agent

An LLM agent in about 25 lines of loop code: the model picks tools,
our code runs them, and a human approves any money transfer.

| File | Purpose |
|------|---------|
| `tools.py` | Mock bank data, three tools, and their JSON schemas |
| `agent.py` | Finished agent (reference) |
| `agent_live.py` | Same file with the loop as TODOs, for live coding |
| `demo_script.md` | The 4 demo prompts in order |

## Setup

```
pip install -r requirements.txt
cp .env.example .env        # then paste your key from console.groq.com
python agent.py
```

To change the model, edit `MODEL` at the top of `agent.py`.

## If the API fails on stage

- **401 / auth error**: check that `.env` exists in this folder and
  contains `GROQ_API_KEY=...`.
- **429 / rate limit**: wait 30 seconds and retry. Keep a second
  Groq key in your notes and swap it into `.env`.
- **Model not found / deprecated**: set `MODEL` to another tool-calling
  model listed at console.groq.com/docs/models
  (e.g. `openai/gpt-oss-20b`).
- **SSL / certificate error** (corporate networks like Zscaler):
  `truststore` in `agent.py` already handles this by using the
  Windows certificate store. Make sure `pip install -r
  requirements.txt` was run so `truststore` is installed.
- **"Request timed out"**: a network blip. The agent prints one line
  and keeps running, so just retype the prompt. A phone hotspot
  avoids the corporate proxy entirely.
- **No internet**: switch to a pre-recorded terminal run of
  `agent.py` and narrate over it. Record one the day before.
