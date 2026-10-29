import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

API_TOKEN = os.getenv("API_TOKEN", "change-me")
TOTAL_RECORDS = int(os.getenv("TOTAL_RECORDS", "1000"))

# account_id must match Salesforce Account Ids (18 chars) so the Logic River join works.
# Set ACCOUNT_IDS="001xx...,001yy..." on Render to use your real sf_account_raw ids.
_env_ids = [a.strip() for a in os.getenv("ACCOUNT_IDS", "").split(",") if a.strip()]
_rng = random.Random(42)  # fixed seed -> same data on every restart (stable MERGE keys)
ALPHANUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
ACCOUNT_IDS = _env_ids or ["001" + "".join(_rng.choices(ALPHANUM, k=15)) for _ in range(25)]

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
app = FastAPI(title="Mock Transactions API")
bearer = HTTPBearer()


def auth(c: HTTPAuthorizationCredentials = Depends(bearer)):
    if c.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/transactions", dependencies=[Depends(auth)])
def transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    modified_since: Optional[str] = Query(None, description="ISO UTC, e.g. 2026-09-01T00:00:00Z"),
):
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
