"""Mock banking tools the agent can call."""

MOCK_DB = {
    "ACC-1001": {
        "owner": "Pranav",
        "balance": 5250.00,
        "transactions": [
            {"date": "2026-09-01", "desc": "Salary", "amount": 4000.00},
            {"date": "2026-09-03", "desc": "Rent", "amount": -1500.00},
            {"date": "2026-09-07", "desc": "Groceries", "amount": -120.45},
            {"date": "2026-09-10", "desc": "Electric bill", "amount": -85.20},
            {"date": "2026-09-14", "desc": "Coffee shop", "amount": -6.75},
            {"date": "2026-09-18", "desc": "Refund", "amount": 42.00},
            {"date": "2026-09-22", "desc": "Gym", "amount": -45.00},
            {"date": "2026-09-27", "desc": "Restaurant", "amount": -64.30},
        ],
    },
    "ACC-2002": {
        "owner": "Bob",
        "balance": 820.50,
        "transactions": [
            {"date": "2026-09-02", "desc": "Freelance pay", "amount": 900.00},
            {"date": "2026-09-04", "desc": "Phone bill", "amount": -40.00},
            {"date": "2026-09-08", "desc": "Bookstore", "amount": -32.99},
            {"date": "2026-09-12", "desc": "Groceries", "amount": -76.10},
            {"date": "2026-09-15", "desc": "Streaming", "amount": -15.99},
            {"date": "2026-09-19", "desc": "Gift from Mom", "amount": 100.00},
            {"date": "2026-09-23", "desc": "Taxi", "amount": -23.40},
            {"date": "2026-09-28", "desc": "Pharmacy", "amount": -18.25},
        ],
    },
    "ACC-3003": {
        "owner": "Charlie",
        "balance": 1340.75,
        "transactions": [
            {"date": "2026-09-01", "desc": "Salary", "amount": 2200.00},
            {"date": "2026-09-05", "desc": "Rent", "amount": -950.00},
            {"date": "2026-09-09", "desc": "Groceries", "amount": -88.60},
            {"date": "2026-09-13", "desc": "Internet bill", "amount": -49.99},
            {"date": "2026-09-17", "desc": "Cinema", "amount": -24.00},
            {"date": "2026-09-21", "desc": "Sold old bike", "amount": 150.00},
            {"date": "2026-09-25", "desc": "Fuel", "amount": -61.40},
            {"date": "2026-09-29", "desc": "Bakery", "amount": -12.30},
        ],
    },
}


def get_balance(account_id):
    account = MOCK_DB.get(account_id)
    if account is None:
        return {"error": f"Account {account_id} not found"}
    return {"account_id": account_id, "balance": account["balance"]}


def get_transactions(account_id, limit=5):
    account = MOCK_DB.get(account_id)
    if account is None:
        return {"error": f"Account {account_id} not found"}
    limit = int(limit)
    recent = account["transactions"][-limit:]
    recent = list(reversed(recent))  # newest first
    return {"account_id": account_id, "transactions": recent}


def check_transfer(from_account, to_account, amount):
    """Return an error dict if the transfer can't happen, else None."""
    amount = float(amount)
    if from_account not in MOCK_DB:
        return {"error": f"Account {from_account} not found"}
    if to_account not in MOCK_DB:
        return {"error": f"Account {to_account} not found"}
    if from_account == to_account:
        return {"error": "Cannot transfer to the same account"}
    if amount <= 0:
        return {"error": "Amount must be positive"}
    if MOCK_DB[from_account]["balance"] < amount:
        return {"error": "Insufficient funds"}
    return None


def transfer_money(from_account, to_account, amount):
    error = check_transfer(from_account, to_account, amount)
    if error:
        return error

    amount = float(amount)
    MOCK_DB[from_account]["balance"] -= amount
    MOCK_DB[to_account]["balance"] += amount
    return {
        "status": "success",
        "from_account": from_account,
        "to_account": to_account,
        "amount": amount,
        "new_balance": MOCK_DB[from_account]["balance"],
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Get the current balance of a bank account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account ID, e.g. ACC-1001",
                    },
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Get the most recent transactions, newest first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account ID, e.g. ACC-1001",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "How many transactions to return",
                    },
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_money",
            "description": "Transfer money from one account to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {"type": "string"},
                    "to_account": {"type": "string"},
                    "amount": {
                        "type": "number",
                        "description": "Amount in dollars",
                    },
                },
                "required": ["from_account", "to_account", "amount"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "get_balance": get_balance,
    "get_transactions": get_transactions,
    "transfer_money": transfer_money,
}
