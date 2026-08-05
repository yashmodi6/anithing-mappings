# Contributing to Anithing Mappings

First off, thank you for considering contributing to Anithing Mappings! This repository powers the master database for the [anithing-api](https://github.com/yashmodi6/anithing-api) and relies on community help to map and verify anime data correctly.

## How to Contribute Mappings

The easiest way to contribute is by helping us manually verify and map anime that haven't been mapped yet. We have a built-in GUI to make this process incredibly easy.

### 1. Set Up Locally

Clone the repository and install the Python dependencies:

```bash
git clone https://github.com/yashmodi6/anithing-mappings.git
cd anithing-mappings
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Verification GUI

Start the automation orchestrator to fetch the latest data and launch the GUI:

```bash
cd automation
python main.py
```
*This will open the React app in your browser at `http://localhost:5000`.*

### 3. Verify Anime

1. In the UI, you will see unverified anime.
2. Check if the provided TMDB, TVDB, and MAL IDs match the AniList entry.
3. If they are incorrect, click the ID to update it.
4. Click **Verify** when the mappings are correct.

This will automatically save your changes to the `assets/mapping-edits.json` file.

### 4. Submit a Pull Request

Once you have verified a batch of anime, you can submit your changes back to us:

1. Fork the repository.
2. Commit your changes: `git commit -am 'Update anime mappings'`
3. Push to your fork: `git push origin main`
4. Open a Pull Request on GitHub.

## Reporting Issues

If you spot an incorrect mapping but can't run the tool yourself, please open an **Issue** on GitHub providing:
- The AniList ID of the anime.
- The correct IDs for TMDB, TVDB, or MAL.

Thank you for helping us build the ultimate anime database!
