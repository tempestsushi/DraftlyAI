from __future__ import annotations

from .db.supabase import SupabaseStore, create_supabase_store

Store = SupabaseStore

store = create_supabase_store()
