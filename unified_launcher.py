import winreg
import os
import subprocess
import tkinter as tk
from pathlib import Path
from PIL import image, ImageOps, ImageTk

def parse_vdf_pairs(file_path: Path) -> list[tuple[str, str]]:
    pairs = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")

    for line in text.splitlines():
        parts = line.split('"')
        if len(parts) >= 5:
            key = parts[1].strip()
            value = parts[3].strip()
            pairs.append((key, value))
    return pairs

def find_steam_art(steam_path: Path, appid: str) -> tuple[str | None, str | None]:
    cache_dir = steam_path / "appcache" / "librarycache"
    banner_path = None
    icon_path = None

    banner_candidates = [
        cache_dir / f"{appid}_library_600x900.jpg",
        cache_dir / f"{appid}_header.jpg",
        cache_dir / appid / "library_600x900.jpg",
        cache_dir / appid / "header.jpg",
    ]

    for candidate in banner_candidates:
        if candidate.exists():
            banner_path = str(candidate)
            break

    icon_candidates = [
        cache_dir / f"{appid}_icon.jpg",
        cache_dir / appid / "icon.jpg",
    ]

    for candidate in icon_candidates:
        if candidate.exists:
            icon_path = str(candidate)
            break

    return banner_path, icon_path