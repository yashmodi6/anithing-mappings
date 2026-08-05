import math
import sqlite3
import httpx
from typing import Callable, Optional, Dict, Any
from config import ID_CHUNK_SIZE
from db import get_local_ids_in_range, get_dead_ids_in_range, mark_dead_ids, save_anime_batch
from api import AsyncRateLimiter, fetch_page_async

async def run_gap_filler_async(
    conn: sqlite3.Connection,
    max_id: int,
    rate_limiter: AsyncRateLimiter,
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
) -> int:
    total_saved = 0
    total_chunks = math.ceil(max_id / ID_CHUNK_SIZE)
    if progress_callback:
        progress_callback("gap_filler", {"message": "Starting Gap Filler to recover missing anime..."})
        
    async with httpx.AsyncClient(timeout=15.0) as client:
        for chunk_idx in range(1, total_chunks + 1):
            start_id = (chunk_idx - 1) * ID_CHUNK_SIZE + 1
            end_id = min(chunk_idx * ID_CHUNK_SIZE, max_id)
            
            local_ids = set(get_local_ids_in_range(conn, start_id, end_id))
            dead_ids = set(get_dead_ids_in_range(conn, start_id, end_id))
            all_possible = set(range(start_id, end_id + 1))
            
            missing_ids = list(all_possible - local_ids - dead_ids)
            if not missing_ids:
                continue
                
            if progress_callback:
                progress_callback("gap_filler", {"message": f"Chunk {chunk_idx}/{total_chunks} | Checking {len(missing_ids)} missing IDs"})
                
            found_items = []
            for chunk_page in range(1, 101):
                data = await fetch_page_async(client, chunk_page, missing_ids, progress_callback, rate_limiter)
                media_list = data.get("media", [])
                if not media_list:
                    break
                found_items.extend(media_list)
                page_info = data.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                    
            if found_items:
                save_anime_batch(conn, found_items)
                total_saved += len(found_items)
                if progress_callback:
                    progress_callback("gap_filler", {"message": f"Recovered {len(found_items)} anime in chunk {chunk_idx}"})
                
            found_ids = {m["id"] for m in found_items}
            new_dead = [mid for mid in missing_ids if mid not in found_ids]
            if new_dead:
                mark_dead_ids(conn, new_dead)
                
    if progress_callback:
        progress_callback("gap_filler", {"message": f"Complete. Recovered a total of {total_saved} missing anime!"})
    return total_saved
