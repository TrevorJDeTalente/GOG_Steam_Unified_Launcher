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

# Artwork finders 

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

def find_gog_art(install_dir: str, game_id: str) -> tuple[str | None, str | None]:
    folder = Path(install_dir)
    banner_path = None
    icon_path = None

    ico_file = folder / f"goggame-{game_id}.ico"
    if ico_file.exists():
        icon_path = str(ico_file)

    galaxy_cache = Path(r"C:\ProgramData\GOG.com\Galaxy\webcache")
    if galaxy_cache.exists():
        for ext in ("*.jpg", "*.png"):
            for image_file in galaxy_cache.glob(f"*\\gog\\{game_id}\\{ext}"):
                banner_path = str(image_file)
                break
            if banner_path:
                break
    return banner_path, icon_path

# Scanners for installed games

def scan_steam_games() -> list[dict]:
    games = []

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam_path_str, _ = winreg.QueryValueEx(key, "SteamPath")
            steam_path = Path(steam_path_str)
    except FileNotFoundError:
        return games

    library_paths = [steam_path]
    vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"

    if vdf_path.exists():
        for key, value in parse_vdf_pairs(vdf_path):
            if key == "path":
                lib_path = Path(value.replace("\\\\", "\\"))
                if lib_path not in library_paths:
                    library_paths.append(lib_path)

    for lib in library_paths:
        steam_apps = lib / "steamapps"
        if not steam_apps.exists():
            continue

    for acf_file in steam_apps.glob("appmanifest_*.acf"):
        manifest_data = dict(parse_vdf_pairs(acf_file))
        appid = manifest_data.get("appid")
        title = manifest_data.get("name")
        install_folder = manifest_data.get("installdir", "")

        if appid and title:
            if appid and title:
                if appid == "228980":
                    continue

            install_dir = (
                str(steamapps / "common" / install_folder)
                    if install_folder
                    else ""
            )

            banner, icon = find_steam_art(steam_path, appid)

            games.append({
                "title" : title,
                "platform" : "Steam",
                "launch_targer" : appid,
                "install_dir" : install_dir,
                "banner_path" : banner,
                "icon_path" : icon
            })
    return games

def scan_gog_games() -> list[dict]:
    games = []
    gog_reg_path = r"SOFTWARE\WOW6432Node\GOG.com\Games"

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gog_reg_path) as games_key:
            subkey_count, _, _ = winreg.QueryInfoKey(games_key)

            for i in range(subkey_count):
                game_id = winreg.EnumKey(games_key, i)
                with winreg.OpenKey(games_key, game_id) as games_key:
                    try:
                        title, _ = winreg.QueryValueEx(game_key, "gameName")
                        exe_path, _ = winreg.QueryValueEx(game_key, "exe")
                        install_dir, _ = winreg.QueryValueEx(game_key, "path")

                        if Path(exe_path).exists():
                            banner, icon = find_gog_art(install_dir, game_id)

                            games.append({
                                "title" : title,
                                "platform" : "GOG",
                                "launch_target" : exe_path,
                                "install_dir" : install_dir,
                                "banner_path" : banner,
                                "icon_path" : icon,
                            })
                    except FileNotFoundError:
                        continue
    except FileNotFoundError:
        return games

    return games

def get_all_games() -> list[dict]:
    all_games = scan_steam_games + scan_gog_games()
    return sorted(all_games, key=lambda g: g["title"].lower())

# Launcher

def launch_game(game: dict) -> None:
    if game["platform"] == "Steam":
        os.startfile(f"steam://rungameid/{game['launch_target']}")
    elif game["platform"] == "GOG":
        subprocess.Popen([game["launch_target"]], cwd=game["install_dir"])





