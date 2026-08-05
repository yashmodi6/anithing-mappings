# Subprocess Runner & Clean Output Event Stream Parser

import os
import sys
import time
import subprocess
from typing import Dict, Any
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from utils.ui import console


# Helper: Parse line output from step process and update Rich progress bar
def parse_process_line(line_str: str, step_title: str, progress: Progress, task: int) -> None:
    if "429 Rate Limit" in line_str:
        progress.update(task, description=f"[bold yellow]⚠️ {line_str}[/bold yellow]")
    elif line_str.startswith("CHUNK:"):
        parts = line_str.replace("CHUNK:", "").split()
        chunk_range = parts[0]
        page_info = " ".join(parts[1:])
        progress.update(task, description=f"[bold cyan]{step_title}[/bold cyan] [cyan]Chunk {chunk_range} {page_info}[/cyan]")
    elif line_str.startswith("INCREMENTAL:"):
        page_info = line_str.replace("INCREMENTAL:", "").strip()
        progress.update(task, description=f"[bold cyan]{step_title}[/bold cyan] [cyan]Incremental Sync {page_info}[/cyan]")
    elif line_str.startswith("DOWNLOAD_PROGRESS:"):
        pct = line_str.replace("DOWNLOAD_PROGRESS:", "").strip()
        progress.update(task, description=f"[bold cyan]{step_title}[/bold cyan] [cyan]Downloading Mappings {pct}[/cyan]")
    elif line_str.startswith("MAPPING_PROGRESS:"):
        pct = line_str.replace("MAPPING_PROGRESS:", "").strip()
        progress.update(task, description=f"[bold cyan]{step_title}[/bold cyan] [cyan]Parsing Mappings {pct}[/cyan]")
    elif line_str.startswith("GAP_FILLER:"):
        info = line_str.replace("GAP_FILLER:", "").strip()
        progress.update(task, description=f"[bold cyan]{step_title}[/bold cyan] [magenta]Gap Filler {info}[/magenta]")


# Execute step subprocess and monitor event stream
def run_pipeline_step(step: Dict[str, Any], step_dir: str, clean_mode: bool = False, force_mode: bool = False, clean_graveyard: bool = False) -> float:
    script_path = os.path.join(step_dir, step["script"])
    cmd = [sys.executable, script_path]
    if force_mode:
        cmd.append("--force")
    elif clean_mode:
        cmd.append("--clean")
        
    if clean_graveyard:
        cmd.append("--clean-graveyard")


    start_time = time.time()
    step_title = step["name"]

    # Initialize transient Rich progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"[bold cyan]{step_title}[/bold cyan]...", total=None)

        # Launch step process in non-blocking line-buffered mode
        # Enable pipe streaming with UTF-8 replacement to avoid crash-on-decode errors while actively feeding the live progress bar
        process = subprocess.Popen(
            cmd,
            cwd=step_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        # Read process output line by line
        try:
            for line in process.stdout:
                parse_process_line(line.strip(), step_title, progress, task)
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            console.print(f"\n[bold yellow]◎[/bold yellow] [bold yellow]{step_title}[/bold yellow] [dim]Force stopped by user[/dim]")
            sys.exit(130)
            
        elapsed = round(time.time() - start_time, 2)

    # Print final completion status line with text tick mark
    if process.returncode == 0:
        console.print(f"[bold green]✓[/bold green] [bold white]{step_title}[/bold white] [dim]Finished successfully in {elapsed}s[/dim]")
    # Gracefully handle user-initiated manual interruptions without flagging them as pipeline errors
    elif process.returncode in (130, -2):
        # SIGINT / Ctrl+C — user-initiated stop, not a failure
        console.print(f"[bold yellow]◎[/bold yellow] [bold yellow]{step_title}[/bold yellow] [dim]Stopped by user after {elapsed}s[/dim]")
    else:
        stderr_output = ""
        try:
            stderr_output = process.stderr.read().strip() if process.stderr else ""
        except Exception:
            pass
        console.print(f"[bold red]✗[/bold red] [bold red]{step_title}[/bold red] [dim]Failed (exit {process.returncode}) in {elapsed}s[/dim]")
        if stderr_output:
            console.print(f"[bold red]Error output:[/bold red]")
            console.print(f"[red]{stderr_output}[/red]")

    return elapsed
