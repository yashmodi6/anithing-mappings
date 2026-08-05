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

## Credits

This pipeline relies on the incredible work of several community-driven databases and projects. Huge thanks to:

- **[AniList](https://anilist.co/)**
- **[The Movie Database (TMDB)](https://www.themoviedb.org/)**
- **[TheTVDB](https://thetvdb.com/)**
- **[MyAnimeList (MAL)](https://myanimelist.net/)**
- **[AniDB](https://anidb.net/)**
- **[AniBridge](https://github.com/anibridge/anibridge-mappings)**

<!-- STATS_START -->
## Database Coverage & Stats

### Provider Coverage
| Provider Category | Total AniList | Mapped Count | Missing / Left |
| :--- | --: | --: | --: |
| MyAnimeList (MAL) | 22,473 | 160 (0.7%) | 22,313 (99.3%) |
| AniDB | 22,473 | 0 (0.0%) | 22,473 (100.0%) |
| TVDB (Show/Movie) | 22,473 | 160 (0.7%) | 22,313 (99.3%) |
| TMDB (Show/Movie) | 22,473 | 160 (0.7%) | 22,313 (99.3%) |
| Step 3 Verified (Manual) | 22,473 | 160 (0.7%) | 22,313 (99.3%) |

### Anime Status Breakdown
| Anime Status | Total Anime | Total Verified | Percentage |
| :--- | --: | --: | --: |
| FINISHED | 21,429 | 160 | 0.7% |
| NOT_YET_RELEASED | 693 | 0 | 0.0% |
| RELEASING | 312 | 0 | 0.0% |
| CANCELLED | 39 | 0 | 0.0% |

<!-- STATS_END -->
