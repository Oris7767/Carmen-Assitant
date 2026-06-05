"""
supabase_client.py — Shared Supabase client for horoscope orders.
"""

import os
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent

_SUPABASE = None

def get_supabase():
    """Get Supabase client (singleton)."""
    global _SUPABASE
    if _SUPABASE is not None:
        return _SUPABASE
    
    from supabase import create_client
    
    creds_path = BASE_DIR / ".supabase_creds.json"
    if not creds_path.exists():
        raise RuntimeError("Missing .supabase_creds.json")
    
    with open(creds_path) as f:
        cfg = json.load(f)
    
    _SUPABASE = create_client(cfg['url'], cfg['anon_key'])
    return _SUPABASE


def update_order_status(order_id: str, status: str, **kwargs):
    """Update a horoscope order's status and optional fields."""
    if not order_id:
        return
    
    supabase = get_supabase()
    updates = {"pdf_status": status}
    
    if "pdf_url" in kwargs:
        updates["pdf_url"] = kwargs["pdf_url"]
    if "notes" in kwargs:
        updates["notes"] = kwargs["notes"]
    if "payment_status" in kwargs:
        updates["payment_status"] = kwargs["payment_status"]
    
    result = supabase.table('horoscope_orders')\
        .update(updates)\
        .eq('order_id', order_id)\
        .execute()
    
    return result.data


def get_order(order_id: str):
    """Get an order by order_id."""
    supabase = get_supabase()
    result = supabase.table('horoscope_orders')\
        .select('*')\
        .eq('order_id', order_id)\
        .limit(1)\
        .execute()
    
    if result.data:
        return result.data[0]
    return None
