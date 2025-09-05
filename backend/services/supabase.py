import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger("supabase")

_supabase_client: Optional[Client] = None

def init_supabase() -> Optional[Client]:
    global _supabase_client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE_URL/SUPABASE_KEY not set; Supabase features disabled")
        _supabase_client = None
        return None

    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")
        return _supabase_client
    except Exception as exc:
        logger.error(f"Supabase initialization failed: {exc}")
        _supabase_client = None
        return None

def get_supabase() -> Client:
    if _supabase_client is None:
        # Attempt lazy init
        init_supabase()
    if _supabase_client is None:
        raise RuntimeError("Supabase client is not initialized")
    return _supabase_client


