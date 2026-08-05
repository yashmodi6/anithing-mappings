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


# Helper: Query Step 2 SQLite database for provider mapping counts
def query_step2_stats(step2_db: str) -> Dict[str, int]:
    stats = {"total_mapped": 0, "mal": 0, "anidb": 0, "tvdb": 0, "tmdb": 0}
    if not os.path.exists(step2_db):
        return stats
    try:
        conn = sqlite3.connect(step2_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mappings")
        stats["total_mapped"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM mappings WHERE mal_id IS NOT NULL AND mal_id != 0")
        stats["mal"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM mappings WHERE anidb_id IS NOT NULL AND anidb_id != 0")
        stats["anidb"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM mappings WHERE tvdb_show_id IS NOT NULL OR tvdb_movie_id IS NOT NULL")
        stats["tvdb"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM mappings WHERE tmdb_show_id IS NOT NULL OR tmdb_movie_id IS NOT NULL")
        stats["tmdb"] = cursor.fetchone()[0]

        conn.close()
    except Exception:
        pass
    return stats


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


# Render cross-provider coverage summary table
def render_coverage_table(base_total: int, step2_data: Dict[str, int], verified_count: int) -> None:
    table = Table(title="📊 ANILIST CROSS-PROVIDER MAPPING COVERAGE", border_style="cyan", header_style="bold magenta")
    table.add_column("Provider Category", style="bold cyan", width=22)
    table.add_column("Total AniList", style="bold white", justify="right")
    table.add_column("Mapped Count", style="bold green", justify="right")
    table.add_column("Missing / Left", style="bold yellow", justify="right")

    providers = [
        ("MyAnimeList (MAL)", step2_data.get("mal", 0)),
        ("AniDB", step2_data.get("anidb", 0)),
        ("TVDB (Show/Movie)", step2_data.get("tvdb", 0)),
        ("TMDB (Show/Movie)", step2_data.get("tmdb", 0)),
        ("Step 3 Verified (Manual)", verified_count)
    ]

    for name, mapped in providers:
        missing = max(0, base_total - mapped)
        mapped_pct = f"({(mapped / base_total * 100):.1f}%)" if base_total > 0 else ""
        missing_pct = f"({(missing / base_total * 100):.1f}%)" if base_total > 0 else ""

        table.add_row(
            name,
            f"{base_total:,}",
            f"{mapped:,} {mapped_pct}",
            f"{missing:,} {missing_pct}"
        )

    console.print()
    console.print(table)


# Render status breakdown summary table
def render_status_table(status_breakdown: Dict[str, int]) -> None:
    if not status_breakdown:
        return
    status_table = Table(title="📺 ANIME STATUS BREAKDOWN", border_style="cyan", header_style="bold magenta")
    status_table.add_column("Anime Status", style="bold cyan", width=22)
    status_table.add_column("Total Count", style="bold white", justify="right")
    status_table.add_column("Percentage", style="bold green", justify="right")

    total_status_count = sum(status_breakdown.values())
    for st_name, count in status_breakdown.items():
        pct = f"{(count / total_status_count * 100):.1f}%" if total_status_count > 0 else "0%"
        status_table.add_row(st_name, f"{count:,}", pct)

    console.print()
    console.print(status_table)


# Main render statistics summary controller
def render_stats_summary(automation_dir: str) -> None:
    output_dir = os.path.join(automation_dir, "output")
    step1_db = os.path.join(output_dir, "step1_anilist", "anime.db")
    step2_db = os.path.join(output_dir, "step2_anibridge", "anibridge.db")
    step3_db = os.path.join(output_dir, "step3_verified", "verified.db")

    total_anilist, status_breakdown = query_step1_stats(step1_db)
    step2_data = query_step2_stats(step2_db)
    verified_count = query_step3_stats(step3_db)

    base_total = max(total_anilist, step2_data.get("total_mapped", 0))

    if base_total > 0:
        render_coverage_table(base_total, step2_data, verified_count)

    if status_breakdown:
        render_status_table(status_breakdown)


# Render pipeline finish message
def render_pipeline_finish(total_elapsed: float, automation_dir: str) -> None:
    render_stats_summary(automation_dir)
    console.print(f"\n[bold cyan]✨ All pipeline steps finished in {total_elapsed}s.[/bold cyan]")
