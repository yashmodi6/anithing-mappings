git add .
git commit -m "feat: decouple mapping architecture, UI overhaul & implement format-based json splits

- Split monolithic mapping JSON into format-specific files (tv, movie, special, etc.)
- Extracted heavy data transformations into core/transformers.py and services/episode_service.py
- Re-architected frontend: extracted WorkspaceView, decoupled state, and improved layout 
- Completely overhauled Provider UI: added rich poster preview cards and dynamic multi-mapping support per provider
- Simplified mapping UI: merged scopes into single unified inputs and removed redundant UI fields
- Added TV Show / Movie toggle dropdown directly in the TMDB/TVDB input rows for explicit overriding
- Added Delete (trash) button next to Check button for easy mapping removal
- Added local _dirty UI state to clearly show when TMDB/TVDB check is required
- Expanded skip reasons dropdown and cleaned up inline styles
- Updated pre-commit stats script to parse new split JSON schemas"
git push
