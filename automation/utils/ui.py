# Rich TUI Display Components for Orchestrator

import os
import sqlite3
from typing import Dict, Any, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# Render orchestrator header panel
def render_header(clean_mode: bool) -> None:
    console.clear()
    mode_text = "[bold red]CLEAN FULL SCRAPE[/bold red]" if clean_mode else "[bold green]FAST INCREMENTAL SYNC[/bold green]"
    console.print(
        Panel(
            f"[bold cyan]ANITHING AUTOMATION PIPELINE[/bold cyan]\n[dim]Master Orchestrator Dashboard[/dim] | Mode: {mode_text}",
            border_style="cyan"
        )
    )


# Helper: Query Step 1 SQLite database for anime count and status breakdown
def query_step1_stats(step1_db: str) -> Tuple[int, Dict[str, int]]:
    total = 0
    status_breakdown: Dict[str, int] = {}
    if not os.path.exists(step1_db):
        return total, status_breakdown
    try:
        conn = sqlite3.connect(step1_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM anime")
        row = cursor.fetchone()
        total = row[0] if row else 0

        cursor.execute("""
            SELECT COALESCE(NULLIF(status, ''), 'UNKNOWN') as st, COUNT(*) 
            FROM anime 
            GROUP BY st 
            ORDER BY COUNT(*) DESC
        """)
        for r in cursor.fetchall():
            status_breakdown[r[0]] = r[1]
        conn.close()
    except Exception:
        pass
    return total, status_breakdown



# Helper: Query Step 3 SQLite database for manual verification count
def query_step3_stats(step3_db: str) -> int:
    if not os.path.exists(step3_db):
        return 0
    try:
        conn = sqlite3.connect(step3_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM verified_anime WHERE manual_checked = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0




# Render status breakdown summary table
def render_status_table(status_breakdown: Dict[str, int], verified_status_breakdown: Dict[str, int]) -> None:
    if not status_breakdown:
        return
    status_table = Table(title="📺 ANIME STATUS BREAKDOWN", border_style="cyan", header_style="bold magenta")
    status_table.add_column("Anime Status", style="bold cyan", width=22)
    status_table.add_column("Total Anime", style="bold white", justify="right")
    status_table.add_column("Total Verified", style="bold green", justify="right")
    status_table.add_column("Percentage", style="bold yellow", justify="right")

    for st_name, total_count in sorted(status_breakdown.items(), key=lambda x: x[1], reverse=True):
        verified_count = verified_status_breakdown.get(st_name, 0)
        pct = f"{(verified_count / total_count * 100):.1f}%" if total_count > 0 else "0%"
        status_table.add_row(st_name, f"{total_count:,}", f"{verified_count:,}", pct)

    console.print()
    console.print(status_table)


# Helper: Query Verified Anime Status breakdown by joining with Step 1
def query_verified_status_breakdown(step1_db: str, step3_db: str) -> Dict[str, int]:
    breakdown = {}
    if not os.path.exists(step1_db) or not os.path.exists(step3_db):
        return breakdown
    try:
        conn = sqlite3.connect(step3_db)
        conn.execute(f"ATTACH DATABASE '{step1_db}' AS step1")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(NULLIF(s1.status, ''), 'UNKNOWN') as st, COUNT(v.anilist_id)
            FROM verified_anime v
            JOIN step1.anime s1 ON v.anilist_id = s1.anilist_id
            WHERE v.manual_checked = 1
            GROUP BY st
        """)
        for r in cursor.fetchall():
            breakdown[r[0]] = r[1]
        conn.close()
    except Exception:
        pass
    return breakdown


# Main render statistics summary controller
def render_stats_summary(automation_dir: str) -> None:
    output_dir = os.path.join(automation_dir, "output")
    step1_db = os.path.join(output_dir, "step1_anilist", "anime.db")
    step2_db = os.path.join(output_dir, "step2_anibridge", "anibridge.db")
    step3_db = os.path.join(output_dir, "step3_verified", "verified.db")

    total_anilist, status_breakdown = query_step1_stats(step1_db)
    verified_status_breakdown = query_verified_status_breakdown(step1_db, step3_db)
    base_total = total_anilist

    if status_breakdown:
        render_status_table(status_breakdown, verified_status_breakdown)


# Render pipeline finish message
def render_pipeline_finish(total_elapsed: float, automation_dir: str) -> None:
    render_stats_summary(automation_dir)
    console.print(f"\n[bold cyan]✨ All pipeline steps finished in {total_elapsed}s.[/bold cyan]")
