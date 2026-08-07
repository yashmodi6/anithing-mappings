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

> Note: Most of the codebase up to Step 3 was generated with AI assistance. I have personally tested the implementation, and everything is working correctly at the moment. Over the next couple of weeks (starting from 6 August 2026), I plan to revisit the code, review it thoroughly, and perform manual optimizations and refactoring.»

> Contributions are welcome in the meantime, especially for anime mappings. When verifying mappings, only confirm entries where both the release date and the media type match across providers. If either the release date or the media type does not match—even if there are known edge cases—do not verify that mapping. Simply skip it and move on to the next entry.»

> Contributions to this repository are encouraged rather than cloning separate forks, as working in a single shared repository makes collaboration easier and progress faster for everyone. While the API has already been designed, I will provide regular database dumps that contributors can use to keep their local data up to date. The long-term goal is for this to be a community-driven project.»

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
## 📊 Database Coverage & Stats

- **Total Anime Tracked:** 22,475
- **Total Verified:** 483 (2.1%)
- **Anibridge Corrections:** 150 mappings fixed!
- **Skipped Anime:** [View Skipped Entries](SKIPPED.md)

### ✅ Verified Database Quality
*(Indicates how complete the mapping is for anime that have been manually verified)*

| Provider | Successfully Mapped | Missing / No Match |
| :--- | --: | --: |
| **TMDB** | 483 | 0 |
| **TVDB** | 482 | 1 |
| **MAL** | 483 | 0 |

### 🎬 Format Breakdown
*(Shows verification progress across different media types)*

| Format | Total in AniList | Verified Here | Progress |
| :--- | --: | --: | --: |
| **TV** | 5,000 | 70 | ![1.4%](https://geps.dev/progress/1.4) |
| **MOVIE** | 4,102 | 413 | ![10.1%](https://geps.dev/progress/10.1) |
| **OVA** | 3,884 | 0 | ![0.0%](https://geps.dev/progress/0.0) |
| **ONA** | 3,451 | 0 | ![0.0%](https://geps.dev/progress/0.0) |
| **MUSIC** | 2,732 | 0 | ![0.0%](https://geps.dev/progress/0.0) |
| **SPECIAL** | 1,848 | 0 | ![0.0%](https://geps.dev/progress/0.0) |
| **TV_SHORT** | 1,375 | 0 | ![0.0%](https://geps.dev/progress/0.0) |
| **UNKNOWN** | 83 | 0 | ![0.0%](https://geps.dev/progress/0.0) |

<!-- STATS_END -->
