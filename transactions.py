import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

TOTAL_RECORDS = int(os.getenv("TOTAL_RECORDS", "1000"))

# Real Salesforce Account Ids (18 chars) so the Logic River join works.
SF_ACCOUNT_IDS = [
    "001g80000179bVGAAY", "001g8000017BNxdAAG", "001g8000017BNXpAAO",
    "001g8000018cK6LAAU", "001g8000018cK6MAAU", "001g8000018cK6NAAU",
    "001g8000018cK6OAAU", "001g8000018cK6PAAU", "001g8000018cK6QAAU",
    "001g8000018cK6RAAU", "001g8000018cK6SAAU", "001g8000018cK6TAAU",
    "001g8000018cK6UAAU", "001g8000018dLQrAAM", "001g8000018dLQsAAM",
    "001g8000018dLQtAAM", "001g8000018dLQuAAM", "001g8000018dLQvAAM",
    "001g8000018dLQwAAM", "001g8000018dLQxAAM", "001g8000018dLQyAAM",
    "001g8000018dLQzAAM", "001g8000018dLR0AAM", "001dN000014u3d7QAA",
    "001dN000014u3d8QAA", "001dN000014u3d9QAA", "001dN000014u3dAQAQ",
    "001dN000014u3dBQAQ", "001dN000014u3dCQAQ", "001dN000014u3dDQAQ",
    "001dN000014u3dEQAQ", "001dN000014u3dFQAQ", "001dN000014u3dGQAQ",
    "001dN000014u3dHQAQ", "001dN000014u3dIQAQ", "001dN000014u3dJQAQ",
    "001dN000014u3dKQAQ", "001dN000014u3dLQAQ", "001dN000014u3dMQAQ",
    "001dN000014u3dNQAQ", "001dN000014u3dOQAQ",
]

# Optional override: set ACCOUNT_IDS="id1,id2,..." on Render to use a different list.
_env_ids = [a.strip() for a in os.getenv("ACCOUNT_IDS", "").split(",") if a.strip()]
ACCOUNT_IDS = _env_ids or SF_ACCOUNT_IDS

_rng = random.Random(42)  # fixed seed -> same data on every restart (stable MERGE keys)

TYPES = ["PURCHASE", "REFUND", "SUBSCRIPTION"]
STATUSES = ["SUCCESS", "FAILED", "PENDING"]
METHODS = ["CREDIT_CARD", "WIRE", "CRYPTO", "PREPAID"]
PRODUCTS = [("SKU-1001", "Analytics Suite"), ("SKU-1002", "Data Connector"),
            ("SKU-1003", "Premium Support"), ("SKU-1004", "Storage Add-on"),
            ("SKU-1005", "Training Package")]

ANCHOR = datetime(2026, 10, 30, tzinfo=timezone.utc)  # fixed so dates don't shift on restart


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build():
    rows = []
    for _ in range(TOTAL_RECORDS):
        pid, pname = _rng.choice(PRODUCTS)
        qty = _rng.randint(1, 10)
        amount = round(_rng.uniform(20, 1500), 2)
        txn_dt = ANCHOR - timedelta(seconds=_rng.randint(0, 300 * 86400))  # up to ~300 days back
        created = txn_dt + timedelta(seconds=_rng.randint(1, 3600))
        modified = created + timedelta(seconds=_rng.randint(0, 7 * 86400))
        rows.append({
            "transaction_id": str(uuid.UUID(int=_rng.getrandbits(128), version=4)),
            "account_id": _rng.choice(ACCOUNT_IDS),
            "transaction_date": _iso(txn_dt),
            "transaction_type": _rng.choices(TYPES, weights=[80, 5, 15])[0],
            "amount": amount,
            "currency": _rng.choices(["USD", "EUR", "GBP"], weights=[70, 20, 10])[0],
            "status": _rng.choices(STATUSES, weights=[80, 10, 10])[0],
            "payment_method": _rng.choice(METHODS),
            "product_id": pid,
            "product_name": pname,
            "quantity": qty,
            "tax_amount": round(amount * qty * 0.08, 2),
            "discount_amount": round(amount * qty * _rng.choice([0, 0, 0.05, 0.1]), 2),
            "created_date": _iso(created),
            "last_modified_date": _iso(modified),
        })
    rows.sort(key=lambda r: r["last_modified_date"])  # stable order for pagination/incremental
    return rows


DATA = _build()


def get_transactions(page: int, page_size: int, modified_since: Optional[str] = None):
    rows = DATA
    if modified_since:
        rows = [r for r in rows if r["last_modified_date"] >= modified_since]
    start = (page - 1) * page_size
    chunk = rows[start:start + page_size]
    return {
        "page": page,
        "page_size": page_size,
        "total": len(rows),
        "has_more": start + page_size < len(rows),
        "data": chunk,
    }
