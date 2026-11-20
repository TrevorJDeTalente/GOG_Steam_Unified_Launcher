# Unified Game Launcher

A lightweight, standalone Windows desktop application built in Python that automatically detects and unifies locally installed Steam and GOG games into a single, searchable interface.

# Why I Was Inspired To Built This

I built this utility to solve my own daily friction: a fast, offline-first launcher that reads directly from my Windows system files and gets me into any game with a single click. As an almost daily user of both GOG and Steam, it meant constantly switching between different desktop clients. Other solutions seemed to tend to require linking online accounts or use of web APIs.


# Demonstration (assets/launchergif.gif)


---

# Features

- **Automatic Library Discovery:** Scans the Windows Registry and local configuration files to detect installed Steam and GOG games automatically.
- **Multi-Drive Steam Support:** Parses Valve's `libraryfolders.vdf` to locate games installed across secondary hard drives and SSDs.
- **Local Artwork & Icon Extraction:** Pulls cached `600x900` vertical cover banners, headers, and `.ico` files directly from Steam's `librarycache`, GOG Galaxy's `webcache`, and game installation folders.
- **Instant Live Search:** Filters your combined game library in real time as you type.
- **One-Click Launching:** Boots Steam titles cleanly via the `steam://rungameid/` protocol (preserving cloud saves and overlays) and launches GOG titles directly from their working directories.

---

# How It Works

Instead of relying on third-party web APIs, this launcher interacts directly with the Windows operating system:

1. **Registry Inspection (`winreg`):** Queries `HKEY_CURRENT_USER\Software\Valve\Steam` for the root Steam directory and enumerates `HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games` for GOG titles, executable paths, and installation folders.
2. **Custom Manifest Parsing:** Uses native Python string splitting and `pathlib` to extract AppIDs, titles, and folder names from Valve `.vdf` and `appmanifest_*.acf` files without regular expression overhead.
3. **Dynamic Image Fitting (`Pillow`):** Center-crops and scales mixed image formats (`.jpg`, `.png`, `.ico`) to uniform card dimensions using Lanczos resampling (`ImageOps.fit`), with clean text-card fallbacks when local artwork is unavailable.

---

# How to use

# Option 1: Download the Windows Executable
1. Go to the [**Releases**](../../releases) page of this repository.
2. Download the latest `UnifiedGameLauncher.exe`.
3. Double-click to run—no Python installation required.

# Or

**Prerequisites:** Windows 10/11 and Python 3.10+

1. Clone the repository:
   ```bash
   git clone https://github.com
   cd unified-game-launcher
   ```

2. Install the required dependency (`Pillow`):
   ```bash
   pip install pillow
   ```

3. Run the application:
   ```bash
   python launcher.py
   ```

---

# Tech Stack

- **Language:** Python 3
- **GUI Framework:** Tkinter
- **Image Processing:** Pillow (`PIL`)
- **System Integration:** `winreg`, `pathlib`, `subprocess`, `os`
- **Packaging:** PyInstaller

---

# Planned Future Improvements

- Platform filter toggles (`All`, `Steam`, `GOG`)
- Support for Epic Games Store and custom `.exe` shortcuts
- Favorites pinning and recently played sorting

---

## License

This project is open source and available under the [MIT License](LICENSE).
