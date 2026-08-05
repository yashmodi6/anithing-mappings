import os
import json
import math
import sqlite3
import asyncio
import httpx
from typing import Callable, Optional, Dict, Any, List

from config import OUTPUT_DIR, ID_CHUNK_SIZE, PER_PAGE
from db import init_db, get_last_updated_at, save_stats, get_local_timestamp_map, get_max_local_id, save_anime_batch
from api import AsyncRateLimiter, get_max_id_async, fetch_page_async, fetch_incremental_page_async
from gap_filler import run_gap_filler_async

class AniListScraper:
    def __init__(self, output_dir: str = OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        self.db_path = os.path.join(self.output_dir, "anime.db")
        self.stats_path = os.path.join(self.output_dir, "stats.json")

    def estimate_duration(self, clean: bool = False) -> str:
        if clean:
            max_id = asyncio.run(get_max_id_async())
            total_pages = math.ceil(max_id / PER_PAGE)
            est_minutes = round(total_pages / 30, 1)
            return f"~{est_minutes} mins ({total_pages:,} pages / {max_id:,} max ID)"

        if not os.path.exists(self.db_path): return self.estimate_duration(clean=True)
        conn = sqlite3.connect(self.db_path)
        last_updated = get_last_updated_at(conn)
        conn.close()
        if last_updated == 0: return self.estimate_duration(clean=True)
        return "~2-10 secs (incremental sync)"

    def _save_checkpoint(self, data: Dict[str, Any]) -> None:
        try:
            with open(os.path.join(self.output_dir, "scrape_checkpoint.json"), "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception: pass

    def _load_checkpoint(self) -> Dict[str, Any]:
        cp = os.path.join(self.output_dir, "scrape_checkpoint.json")
        if os.path.exists(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f: return json.load(f)
            except Exception: pass
        return {}

    def _delete_checkpoint(self) -> None:
        cp = os.path.join(self.output_dir, "scrape_checkpoint.json")
        if os.path.exists(cp):
            try: os.remove(cp)
            except Exception: pass

    async def _process_chunk_async(self, chunk_idx: int, total_chunks: int, max_id: int, conn: sqlite3.Connection, client: httpx.AsyncClient, rate_limiter: AsyncRateLimiter, progress_callback: Optional[Callable]) -> int:
        start_id = (chunk_idx - 1) * ID_CHUNK_SIZE + 1
        end_id = min(chunk_idx * ID_CHUNK_SIZE, max_id)
        id_list = list(range(start_id, end_id + 1))
        chunk_items = []

        for chunk_page in range(1, 101):
            data = await fetch_page_async(client, chunk_page, id_list, progress_callback, rate_limiter)
            media_list = data.get("media", [])
            if not media_list: break
            chunk_items.extend(media_list)
            
            if progress_callback:
                progress_callback("page_done", {"start_id": start_id, "end_id": end_id, "chunk_idx": chunk_idx, "total_chunks": total_chunks, "chunk_page": chunk_page, "last_page": data.get("pageInfo", {}).get("lastPage", "?"), "items_count": len(media_list)})
            if not data.get("pageInfo", {}).get("hasNextPage"): break

        if chunk_items: save_anime_batch(conn, chunk_items)
        if progress_callback: progress_callback("chunk_done", {"start_id": start_id, "end_id": end_id, "chunk_saved": len(chunk_items)})
        return len(chunk_items)

    async def _async_run_full_scrape(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        checkpoint = self._load_checkpoint()
        start_chunk = checkpoint.get("last_completed_chunk", 0) + 1
        cached_max_id = checkpoint.get("max_id")

        is_fresh_start = (start_chunk == 1)
        conn = init_db(self.output_dir, clean=is_fresh_start)

        max_id = cached_max_id if cached_max_id else await get_max_id_async()
        total_chunks = math.ceil(max_id / ID_CHUNK_SIZE)
        rate_limiter = AsyncRateLimiter(requests_per_minute=30)

        if is_fresh_start: self._save_checkpoint({"max_id": max_id, "last_completed_chunk": 0})
        elif progress_callback: progress_callback("info", {"message": f"Resuming from chunk {start_chunk}/{total_chunks}"})

        async with httpx.AsyncClient(timeout=15.0) as client:
            for chunk_idx in range(start_chunk, total_chunks + 1):
                await self._process_chunk_async(chunk_idx, total_chunks, max_id, conn, client, rate_limiter, progress_callback)
                self._save_checkpoint({"max_id": max_id, "last_completed_chunk": chunk_idx})
                
        # Run Gap Filler immediately after full scrape
        await run_gap_filler_async(conn, max_id, rate_limiter, progress_callback)

        stats = save_stats(conn, self.db_path, self.stats_path)
        conn.close()
        self._delete_checkpoint()
        return stats

    def run_full_scrape(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        return asyncio.run(self._async_run_full_scrape(progress_callback=progress_callback))

    async def _async_run_incremental_sync(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        conn = init_db(self.output_dir, clean=False)
        last_updated_at = get_last_updated_at(conn)

        if last_updated_at == 0:
            conn.close()
            return await self._async_run_full_scrape(progress_callback=progress_callback)

        local_map = get_local_timestamp_map(conn)
        total_saved, page, stop_sync = 0, 1, False
        rate_limiter = AsyncRateLimiter(requests_per_minute=30)

        async with httpx.AsyncClient(timeout=15.0) as client:
            while not stop_sync:
                if page > 100:
                    conn.close()
                    return await self._async_run_full_scrape(progress_callback=progress_callback)

                data = await fetch_incremental_page_async(client, page, progress_callback, rate_limiter)
                media_list = data.get("media", [])
                if not media_list: break

                items_to_save, already_on_page = [], 0
                for item in media_list:
                    aid, u_at = item["id"], item.get("updatedAt") or 0
                    if aid in local_map and u_at <= local_map[aid]: already_on_page += 1
                    else:
                        items_to_save.append(item)
                        local_map[aid] = u_at

                if (already_on_page / len(media_list) if media_list else 1.0) >= 0.90: stop_sync = True

                if items_to_save:
                    save_anime_batch(conn, items_to_save)
                    total_saved += len(items_to_save)

                if progress_callback:
                    progress_callback("incremental_page_done", {"page": page, "last_page": data.get("pageInfo", {}).get("lastPage", "?"), "items_count": len(items_to_save), "total_saved": total_saved, "last_updated_at": last_updated_at})

                if stop_sync or not data.get("pageInfo", {}).get("hasNextPage"): break
                page += 1

            local_max, live_max = get_max_local_id(conn), await get_max_id_async()
            if live_max > local_max:
                new_id_list = list(range(local_max + 1, live_max + 1))
                for chunk_start_idx in range(0, len(new_id_list), ID_CHUNK_SIZE):
                    chunk_ids = new_id_list[chunk_start_idx:chunk_start_idx + ID_CHUNK_SIZE]
                    for batch_start in range(0, len(chunk_ids), PER_PAGE):
                        p_data = await fetch_page_async(client, 1, chunk_ids[batch_start:batch_start + PER_PAGE], progress_callback, rate_limiter)
                        m_list = p_data.get("media", [])
                        if m_list:
                            save_anime_batch(conn, m_list)
                            total_saved += len(m_list)
                            
        # Run gap filler after incremental sync
        live_max = await get_max_id_async()
        await run_gap_filler_async(conn, live_max, rate_limiter, progress_callback)

        if progress_callback: progress_callback("incremental_done", {"total_saved": total_saved, "last_updated_at": last_updated_at})

        stats = save_stats(conn, self.db_path, self.stats_path)
        conn.close()
        return stats

    def run_incremental_sync(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        return asyncio.run(self._async_run_incremental_sync(progress_callback=progress_callback))
