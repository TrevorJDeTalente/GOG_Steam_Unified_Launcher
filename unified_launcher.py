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