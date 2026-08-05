# Anithing Mappings

A Python automation pipeline for scraping, verifying, and mapping anime data across AniList, TMDB, TVDB, and MyAnimeList.

This repository generates the master database used by the [anithing-api](https://github.com/yashmodi6/anithing-api) GraphQL server.

## Structure

- `automation/`: Contains the pipeline scripts.
  - `Step 1`: Scrapes AniList data.
  - `Step 2`: Downloads community mappings (AniBridge).
  - `Step 3`: Manual verification GUI.
- `assets/`: Contains manual override files (e.g. `mapping-edits.json`).

## Quick Start

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run Pipeline (Incremental Sync)
Executes all steps sequentially.
```bash
cd automation
python main.py
```

### 3. Clean Scrape
Wipes local caches for Step 1 and Step 2 and rebuilds them from scratch (preserves human-verified Step 3 database).
```bash
cd automation
python main.py --clean
```

### 4. Clean Graveyard
Forces the gap filler to re-verify every missing ID by wiping the `dead_ids.json` cache.
```bash
cd automation
python main.py --clean-graveyard
```
