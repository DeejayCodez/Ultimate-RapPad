# The Ultimate RapPad v2.0

A Windows desktop songwriting workstation built with Python + PySide6.

## Version 2.0 additions
- Live Rhyme Engine in the Studio: detects the last word on the current editor line and refreshes rhyme suggestions as you type.
- Double-click a live suggestion to insert it at the lyric cursor.
- Closest-syllable-match and all-rhymes display modes.
- One-click GitHub Releases update checker for the packaged Windows application.
- Separate updater helper so Windows can replace the running EXE after the app closes.
- Updated version labels and build process.

## Existing tools
- Dark neon studio interface and animated startup sequence: “Created by DJ” → “Enjoy!” → fade into the app.
- Lyric canvas with live word/line/character counts.
- Rhyme Lab, Word Vault, BPM control, 16-step visual metronome, flow drills, writer prompts, song library.
- Local autosave and JSON session save/open.
- Optional CMU pronunciation dictionary support via `pronouncing`.

## Run from source
Install Python 3.10+ and run:
```powershell
py -m pip install -r requirements.txt
py main.py
```

## Build the Windows app
Double-click `build_windows.bat`. It creates `dist\UltimateRapPad.exe`, `dist\RapPadUpdater.exe`, and `release\UltimateRapPad-Windows.zip`.

## Configure one-click updates
The updater uses GitHub Releases. Before publishing:
1. Create a GitHub repository for the app.
2. Edit `update_config.json` and set `github_owner` and `github_repo`.
3. Build the app again so the configuration ships with the app.
4. Upload `release\UltimateRapPad-Windows.zip` as an asset on a GitHub Release.
5. Name the release tag with a version greater than the app's `APP_VERSION`, for example `v2.0.1`.
6. For future updates, increment `APP_VERSION` in `main.py`, rebuild, and publish a new GitHub Release with the same asset filename.

Users install the first release by extracting the ZIP into a folder and running `UltimateRapPad.exe`. Keep `RapPadUpdater.exe` and `update_config.json` beside it. The app checks the latest GitHub Release when the user clicks **CHECK FOR UPDATES**. If a newer release is found, it downloads the ZIP, closes, replaces the app EXE, and restarts.

Important: automatic updates are intended for the packaged Windows EXE, not `py main.py` source runs. The app's song data remains in `Documents\UltimateRapPad` and is not overwritten by app updates.

## Local data and privacy
Drafts and autosaves are stored locally in `Documents\UltimateRapPad`. The updater contacts GitHub only when the user explicitly clicks **CHECK FOR UPDATES**.
