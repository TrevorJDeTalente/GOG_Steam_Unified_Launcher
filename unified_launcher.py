import winreg
import os
import json
import subprocess
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageOps, ImageTk

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

    # Checking  direct root-level legacy paths first
    direct_banners = [
        cache_dir / f"{appid}_library_600x900.jpg",
        cache_dir / f"{appid}_library_capsule.jpg",
        cache_dir / f"{appid}_header.jpg",
        cache_dir / f"{appid}_library_hero.jpg",
    ]
    for candidate in direct_banners:
        if candidate.exists():
            banner_path = str(candidate)
            break

    # checking inside appid subfolder (handles both direct and hashed subdirectories)
    app_cache_dir = cache_dir / appid
    if not banner_path and app_cache_dir.exists():
        preferred_names = (
            "library_600x900.jpg",
            "library_capsule.jpg",
            "header.jpg",
            "library_hero.jpg",
        )
        for filename in preferred_names:
            matches = list(app_cache_dir.rglob(filename))
            if matches:
                banner_path = str(matches[0])
                break

    # checking icons (root and recursive appid subfolder)
    direct_icons = [
        cache_dir / f"{appid}_icon.jpg",
        cache_dir / f"{appid}_icon.png",
    ]
    for candidate in direct_icons:
        if candidate.exists():
            icon_path = str(candidate)
            break

    if not icon_path and app_cache_dir.exists():
        for filename in ("icon.jpg", "icon.png", "logo.png"):
            matches = list(app_cache_dir.rglob(filename))
            if matches:
                icon_path = str(matches[0])
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

def find_epic_art(install_dir: str):
    folder = Path(install_dir)
    banner_path = None
    icon_path = None

    if folder.exists():
        for ico_file in folder.glob("*.ico"):
            icon_path = str(ico_file)
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
                    str(steam_apps / "common" / install_folder)
                        if install_folder
                        else ""
                )

                banner, icon = find_steam_art(steam_path, appid)

                games.append({
                    "title" : title,
                    "platform" : "Steam",
                    "launch_target" : appid,
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
                with winreg.OpenKey(games_key, game_id) as game_key:
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

def scan_epic_games():
    games = []
    manifests_dir = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests")

    if not manifests_dir.exists():
        return games

    for item_file in manifests_dir.glob("*.item"):
        try:
            data = json.loads(item_file.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        
        title = data.get("DisplayName")
        install_dir = data.get("InstallLocation", "")
        launch_exe = data.get("LaunchExecutable", "")
        namespace = data.get("CatalogNamespace")
        item_id = data.get("CatalogItemId")
        app_name = data.get("AppName")

        # Skipping Unreal Engine editor installations or incomplete manifests

        if not title or not install_dir or not launch_exe:
            continue
        if title.startswith("Unreal Engine"):
            continue
    
        full_exe = Path(install_dir) / launch_exe
        if not full_exe.exists():
            continue

        # Building Epic's native launch URI (fallback to direct .exe if IDs aren't found)

        if namespace and item_id and app_name:
            launch_target = (
                f"com.epicgames.launcher://apps/"
                f"{namespace}%3A{item_id}%3A{app_name}?action=launch&silent=true"
            )
        else:
            launch_target = str(full_exe)

        banner, icon = find_epic_art(install_dir)

        games.append({
            "title" : title,
            "platform": "Epic",
            "launch_target" : launch_target,
            "install_dir" : install_dir,
            "banner_path" : banner,
            "icon_path" : icon
        })
    return games

def get_all_games() -> list[dict]:
    all_games = scan_steam_games() + scan_gog_games() + scan_epic_games()
    return sorted(all_games, key=lambda g: g["title"].lower())

# Launcher

def launch_game(game: dict) -> None:
    if game["platform"] == "Steam":
        os.startfile(f"steam://rungameid/{game['launch_target']}")
    elif game["platform"] == "Epic":
        if game["launch_target"].startswith("com.epicgames.launcher://"):
            os.startfile(game["launch_target"])
        else:
            subprocess.Popen([game["launch_target"]], cwd=game['install_dir'])
    elif game["platform"] == "GOG":
        subprocess.Popen([game["launch_target"]], cwd=game["install_dir"])


class UnifiedLauncherApp:
    CARD_WIDTH = 180
    CARD_HEIGHT = 270
    COLUMNS = 4

    BADGE_COLORS = {
        "Steam" : "#3b82f6",
        "GOG" : "#a855f7",
        "Epic" : "#f59e0b"
    }

    def __init__(self, root: tk.Tk, games: list[dict]):
        self.root = root
        self.all_games = games
        self.current_games = games
        self.current_columns = self.COLUMNS
        self.active_platform = "All"
        self.filter_buttons: dict[str, tk.Button] = {}
        self.image_refs: list[ImageTk.PhotoImage] = []

        self.root.title("Unified Game Launcher")
        self.root.geometry("880x700")
        self.root.configure(bg="#121418")

        self._build_top_bar()
        self._build_scrollable_grid()
        self._apply_filters()

    def _build_top_bar(self) -> None:
        top_bar = tk.Frame(self.root, bg="#1b1f26", pady=12, padx=16)
        top_bar.pack(fill="x")

        self.header_label = tk.Label(
            top_bar,
            text=f"My Library ({len(self.all_games)})",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#1b1f26",
        )
        self.header_label.pack(side="left", padx=(0, 16))

        # Filters for platforms

        filter_frame = tk.Frame(top_bar, bg="#1b1f26")
        filter_frame.pack(side="left")

        for platform in ("All", "Steam", "GOG", "Epic"):
            btn = tk.Button(
                filter_frame,
                text=platform,
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                padx=12,
                pady=4,
                cursor="hand2",
                command=lambda p=platform: self._set_platform_filter(p),
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[platform] = btn

        self._update_filter_button_styles()

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._apply_filters())

        search_entry = tk.Entry(
            top_bar,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg="#262b35",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            width=28,
        )
        search_entry.pack(side="right", ipady=5, padx=(8, 0))

        search_label = tk.Label(
            top_bar,
            text="Search:",
            font=("Segoe UI", 10),
            fg="#9aa5b4",
            bg="#1b1f26",
        )
        search_label.pack(side="right")

    def _set_platform_filter(self, platform: str):
        self.active_platform = platform
        self._update_filter_button_styles()
        self._apply_filters()

    def _update_filter_button_styles(self):
        for platform, btn in self.filter_buttons.items():
            if platform == self.active_platform:
                btn.configure(bg="#3b82f6", fg="#ffffff", activebackground="#2563eb")
            else:
                btn.configure(bg="#262b35", fg="#9aa5b4", activebackground="#323946")

    def _apply_filters(self):
        query = self.search_var.get().strip().lower()
        filtered = self.all_games

        if self.active_platform != "All":
            filtered = [g for g in filtered if g["platform"] == self.active_platform]
        if query:
            filtered = [g for g in filtered if query in g["title"].lower()]
        
        self.current_games = filtered
        self.header_label.configure(text=f"My Library ({len(filtered)})")
        self.canvas.yview_moveto(0)
        self.render_games(self.current_games)

    def _build_scrollable_grid(self) -> None:
        container = tk.Frame(self.root, bg="#121418")
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg="#121418", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.grid_frame = tk.Frame(self.canvas, bg="#121418", padx=16, pady=16)

        self.grid_frame.bind(
            "<Configure>",
            lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0,0), window=self.grid_frame, anchor = "nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),           
        )
    
    def _load_card_image(self, game: dict) -> ImageTk.PhotoImage | None:
        art_path = game["banner_path"] or game["icon_path"]
        if not art_path:
            return None

        try:
            with Image.open(art_path) as img:
                img = img.convert("RGB")
                fitted = ImageOps.fit(
                    img,
                    (self.CARD_WIDTH, self.CARD_HEIGHT),
                    Image.Resampling.LANCZOS
                )
                return ImageTk.PhotoImage(fitted)
        except Exception:
            return None

    def _on_search(self, *args) -> None:
        query = self.search_var.get().strip().lower()
        if not query:
            self.render_games(self.all_games)
            return
        filtered = [g for g in self.all_games if query in g["title"].lower()]
        self.render_games(filtered)

    def _on_canvas_resize(self, event: tk.Event) -> None:
        card_slot_width = self.CARD_WIDTH + 32
        available_width = max(event.width - 32, card_slot_width)
        new_columns = max(1, available_width // card_slot_width)

        if new_columns != self.current_columns:
            self.current_columns = new_columns
            self.render_games(self.current_games)


    def render_games(self, games: list[dict]) -> None:
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.image_refs.clear()

        if not games:
            empty_label = tk.Label(
                self.grid_frame,
                text="No matching games found.",
                font=("Segoe UI", 12),
                fg="#9aa5b4",
                bg="#121418",
            )
            empty_label.grid(row=0, column=0, padx=20, pady=20)
            return

        for idx, game in enumerate(games):
            row = idx // self.current_columns
            col = idx % self.current_columns

            card = tk.Frame(
                self.grid_frame,
                bg="#1e232b",
                padx=6,
                pady=6,
                cursor="hand2",
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            photo = self._load_card_image(game)
            if photo:
                self.image_refs.append(photo)
                art_widget = tk.Label(card, image=photo, bg="#1e232b", cursor="hand2")
            else:
                art_widget = tk.Label(
                    card,
                    text=game["title"],
                    font=("Segoe UI", 11, "bold"),
                    fg="#e2e8f0",
                    bg="#2a313d",
                    wraplength=self.CARD_WIDTH - 20,
                    width=20,
                    height=13,
                    cursor="hand2",
                )
            art_widget.pack()

            badge_color = "#3b82f6" if game["platform"] == "Steam" else "#a855f7"
            platform_label = tk.Label(
                card,
                text=game["platform"].upper(),
                font=("Segoe UI", 8, "bold"),
                fg=badge_color,
                bg="#1e232b",
                cursor="hand2",
            )
            platform_label.pack(anchor="w", pady=(6, 0))

            title_label = tk.Label(
                card,
                text=game["title"],
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#1e232b",
                wraplength=self.CARD_WIDTH,
                justify="left",
                cursor="hand2",
            )
            title_label.pack(anchor="w")

            for widget in (card, art_widget, platform_label, title_label):
                widget.bind("<Button-1>", lambda e, g=game: launch_game(g))

if __name__ == "__main__":
    detected_games = get_all_games()
    app_root = tk.Tk()
    UnifiedLauncherApp(app_root, detected_games)
    app_root.mainloop()