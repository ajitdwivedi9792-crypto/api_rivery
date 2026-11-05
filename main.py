from typing import Optional

from fastapi import Depends, FastAPI, Query

import customers
import transactions
from auth import auth

app = FastAPI(title="Mock API (Transactions + CRM)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/transactions", dependencies=[Depends(auth)])
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    modified_since: Optional[str] = Query(None, description="ISO UTC, e.g. 2026-09-01T00:00:00Z"),
):
    return transactions.get_transactions(page, page_size, modified_since)


@app.get("/v1/customers", dependencies=[Depends(auth)])
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    created_since: Optional[str] = Query(None, description="ISO UTC, e.g. 2026-01-01T00:00:00Z"),
):
    return customers.get_customers(page, page_size, created_since)
