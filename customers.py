"""CRM customer master (NorthStar use case, spec section 3.2). Fields: id, email, country, created_at."""
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

TOTAL_CUSTOMERS = int(os.getenv("TOTAL_CUSTOMERS", "300"))
COUNTRIES = ["United States", "United Kingdom", "Germany", "France",
             "India", "Canada", "Australia", "Japan"]
ANCHOR = datetime(2026, 10, 30, tzinfo=timezone.utc)  # fixed so data is stable across restarts

_rng = random.Random(7)  # own seed: does not affect the transactions data


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


VIP_RATE = float(os.getenv("VIP_RATE", "0.2"))  # share of customers who start as VIP
_vip_rng = random.Random(11)  # separate seed so existing fields don't change


def _build():
    rows = []
    for n in range(1, TOTAL_CUSTOMERS + 1):
        created = ANCHOR - timedelta(seconds=_rng.randint(0, 730 * 86400))
        is_vip = _vip_rng.random() < VIP_RATE
        rows.append({
            "id": f"CUST-{n:05d}",  # use these same ids in orders.customer_id
            "email": f"customer{n:05d}@example.com",
            "country": _rng.choice(COUNTRIES),
            "created_at": _iso(created),
            "is_vip": is_vip,
            "segment": "VIP" if is_vip else None,
        })
    return rows


DATA = _build()


def get_customers(
    page: int,
    page_size: int,
    created_since: Optional[str] = None,
    country: Optional[str] = None,
    is_vip: Optional[bool] = None,
    segment: Optional[str] = None,
):
    rows = DATA
    if created_since:
        rows = [r for r in rows if r["created_at"] >= created_since]
    if country:
        rows = [r for r in rows if r["country"].lower() == country.lower()]
    if is_vip is not None:
        rows = [r for r in rows if r["is_vip"] == is_vip]
    if segment:
        rows = [r for r in rows if r["segment"] == segment]
    start = (page - 1) * page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": len(rows),
        "has_more": start + page_size < len(rows),
        "data": rows[start:start + page_size],
    }


def update_customer(customer_id: str, updates: dict):
    for row in DATA:
        if row["id"] == customer_id:
            row.update(updates)
            return row
    return None
