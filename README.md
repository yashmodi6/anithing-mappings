<div align="center">

# Anithing Mappings


[![License](https://img.shields.io/badge/MIT%20License-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-%233670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-%23000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-%2307405e?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![React](https://img.shields.io/badge/React-%2320232a?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-%23007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-%23646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)

</div>

> [!WARNING]
> **Early Development Warning**: This repository is still in its starting phases and actively being developed. Expect frequent changes.

This repo provides manually verified cross-mappings from AniList to TMDB, TVDB, and MAL, including precise episode-to-episode mappings, filler arc tracking, and media links (posters, banners, backgrounds, etc).

This repository generates the master database used by the [anithing-api](https://github.com/yashmodi6/anithing-api) GraphQL server.

---

## 🏗️ Structure

The pipeline is split into distinct scripts, managed by a central orchestrator.

- 📁 `automation/`: Contains the pipeline scripts.
  - [x] **Step 1**: Scrapes AniList data.
  - [x] **Step 2**: Downloads community mappings (AniBridge).
  - [x] **Step 3**: Manual verification GUI.
  - [ ] **Step 4**: Media fetcher to fetch highest rated media automatically
  - [ ] **Step 5**: Animefiller parser
  - [ ] **Step 6**: Aniskip
  - [ ] **Step 7**: Merging DBs to make the final database
- 📁 `assets/`: Contains manual override files (e.g., `mapping-edits.json`).

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run Pipeline (Incremental Sync)
Executes all available steps sequentially.
```bash
cd automation
python main.py
```

### 3. Clean Scrape
Wipes local caches for Step 1 and Step 2 and rebuilds them from scratch (preserves the human-verified Step 3 database).
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

---

## 🙏 Credits

This pipeline relies on the incredible work of several community-driven databases and projects. Huge thanks to:

- **[AniList](https://anilist.co/)**
- **[The Movie Database (TMDB)](https://www.themoviedb.org/)**
- **[TheTVDB](https://thetvdb.com/)**
- **[MyAnimeList (MAL)](https://myanimelist.net/)**
- **[AniDB](https://anidb.net/)**
- **[AniBridge](https://github.com/anibridge/anibridge-mappings)**

---

<!-- STATS_START -->
## Database Coverage & Stats

### Anime Status Breakdown
| Anime Status | Total Anime | Total Verified | Percentage |
| :--- | --: | --: | --: |
| FINISHED | 21,429 | 196 | 0.9% |
| NOT_YET_RELEASED | 693 | 0 | 0.0% |
| RELEASING | 312 | 0 | 0.0% |
| CANCELLED | 39 | 0 | 0.0% |

<!-- STATS_END -->
