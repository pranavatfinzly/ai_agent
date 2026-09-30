# Demo Script

Run `python agent.py` and type these prompts in order.
Each prompt stands on its own because the agent has no memory between turns.

## 1. Balance (one tool call)

```
What's my balance?
```

Expect: `get_balance` with `ACC-1001`, then **$5,250.00**.
Point out: the model asked for the tool, and *our code* ran it.

## 2. Last 5 transactions (a tool with an optional argument)

```
Show me my last 5 transactions.
```

Expect: `get_transactions` with `limit: 5`. Newest first: Restaurant,
Gym, Refund, Coffee shop, Electric bill.
Point out: the model filled in `limit` from plain English.

## 3. Small transfer, APPROVED (the guardrail says yes)

```
Send $50 to Bob.
```

Expect: `transfer_money` from ACC-1001 to ACC-2002 for 50, then the
approval prompt. Type **`y`**. New balance: **$5,200.00**.
Point out: the model *wanted* to move money, but a human made the call.

## 4. Large transfer, REJECTED (the guardrail says no)

```
Transfer $3000 to Bob.
```

Expect: the approval prompt again. Type **`n`**. The model gets
"User declined. Transfer cancelled." as the tool result and tells
the user the transfer was cancelled.
Point out: rejection is just another tool result, and the model handles it.

## Optional encore (if time allows)

```
What's my balance now?
```

Should still be **$5,200.00**, which proves the rejected transfer never ran.

```
Check my balance, then send Bob 10 percent of it.
```

Watch the loop chain three steps: `get_balance`, then `transfer_money`
with an amount the model *calculated* ($520), then the answer.
Type **`y`**. Point out: one prompt, multiple tool calls, the model
decides the order.

## Things the model may do differently each run

- It sometimes calls `get_balance` before a transfer. That's fine;
  point out that the model decided to check first.
- Its wording changes run to run. The numbers never do, because they
  come from the tools.
