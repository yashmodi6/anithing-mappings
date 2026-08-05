# Master Automation Orchestrator TUI Entrypoint

import os
import sys
import time
import shutil
import argparse
import subprocess

# Base directory setup
AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
if AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, AUTOMATION_DIR)

# Configure UTF-8 encoding for console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from utils.ui import console, render_header, render_pipeline_finish
from utils.runner import run_pipeline_step

# Pipeline steps definition list
STEPS = [
    {
        "id": 1,
        "name": "Step 1: AniList Scraper",
        "folder": "anilist_scraper",
        "script": "main.py"
    },
    {
        "id": 2,
        "name": "Step 2: AniBridge Mappings Downloader",
        "folder": "anibridge_downloader",
        "script": "main.py"
    },
    {
        "id": 3,
        "name": "Step 3: Manual Verification GUI",
        "folder": "manual_checker",
        "script": "main.py"
    }
]


# Wipe temporary scraper caches or force clean all including step 3 verified database
def clean_output_directory(automation_dir: str) -> None:
    output_dir = os.path.join(automation_dir, "output")
    target_dirs = [
        os.path.join(output_dir, "step1_anilist"),
        os.path.join(output_dir, "step2_anibridge")
    ]

    for target_dir in target_dirs:
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception:
                pass
    os.makedirs(output_dir, exist_ok=True)


def build_react_ui():
    ui_dir = os.path.abspath(os.path.join(AUTOMATION_DIR, "manual_checker", "frontend"))
    if not os.path.exists(ui_dir):
        return
    console.print("[cyan]Running React UI build...[/cyan]")
    try:
        process = subprocess.Popen(["npm", "run", "build"], cwd=ui_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        process.wait()
        if process.returncode == 0:
            console.print("[green]React UI built successfully.[/green]")
        else:
            console.print(f"[red]React UI build failed with code {process.returncode}.[/red]")
    except Exception as e:
        console.print(f"[red]Could not build React UI: {e}[/red]")


# Main orchestrator CLI entrypoint
def main():
    parser = argparse.ArgumentParser(description="Master Automation Orchestrator TUI")
    parser.add_argument("--clean", action="store_true", help="Force clean scrape on Step 1 & 2 while preserving Step 3 verified DB")
    parser.add_argument("--clean-graveyard", action="store_true", help="Wipe the dead IDs graveyard to force AniList re-verification of all missing IDs")
    parser.add_argument("--yes", "-y", action="store_true", help="Bypass the confirmation prompt for --clean in CI environments")
    args = parser.parse_args()

    pipeline_start_time = time.time()
    
    # Wipe temporary caches if clean flag is set
    if args.clean:
        if not args.yes:
            console.print("[bold red]WARNING: You are about to wipe the AniList and AniBridge databases and force a full re-scrape![/bold red]")
            response = input("Are you sure you want to proceed? (y/N): ")
            if response.lower() != 'y':
                console.print("[yellow]Aborting clean scrape. Run without --clean to resume.[/yellow]")
                sys.exit(0)
        clean_output_directory(AUTOMATION_DIR)

    # Render dashboard header
    render_header(clean_mode=args.clean)

    # Execute each pipeline step sequentially
    for step in STEPS:
        if step["id"] == 3:
            build_react_ui()

        step_dir = os.path.join(AUTOMATION_DIR, step["folder"])
        script_path = os.path.join(step_dir, step["script"])

        if not os.path.exists(script_path):
            console.print(f"[yellow]Skipping {step['name']} (Script {script_path} not found)[/yellow]")
            continue

        run_pipeline_step(step, step_dir, clean_mode=args.clean, force_mode=False, clean_graveyard=args.clean_graveyard)

    # Calculate total pipeline runtime and render summary statistics
    total_pipeline_elapsed = round(time.time() - pipeline_start_time, 2)
    render_pipeline_finish(total_pipeline_elapsed, AUTOMATION_DIR)



if __name__ == "__main__":
    main()
