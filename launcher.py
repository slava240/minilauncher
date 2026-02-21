"""
MiniLauncher v1.0.0
pip install minecraft-launcher-lib requests
pyinstaller --onefile --windowed --collect-all minecraft_launcher_lib --collect-all requests --name MiniLauncher launcher.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
import sys
import subprocess
import urllib.request
import urllib.parse
import shutil
import webbrowser

# ─── HTTP helpers ─────────────────────────────────────────────────────────────
try:
    import requests as _req
    def http_get(url, params=None, timeout=10):
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        r = _req.get(url, headers={"User-Agent": "MiniLauncher/1.0"}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    def http_download(url, dest, progress_cb=None):
        with _req.get(url, stream=True, timeout=120,
                      headers={"User-Agent": "MiniLauncher/1.0"}) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb and total:
                        progress_cb(done, total)
except ImportError:
    def http_get(url, params=None, timeout=10):
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "MiniLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    def http_download(url, dest, progress_cb=None):
        req = urllib.request.Request(url, headers={"User-Agent": "MiniLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            total = int(r.headers.get("Content-Length", 0))
            done  = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb and total:
                        progress_cb(done, total)

import minecraft_launcher_lib

# ─── Paths ────────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MC_DIR      = os.path.join(BASE_DIR, "minecraft")
SERVERS_DIR = os.path.join(BASE_DIR, "servers")
SETTINGS_F  = os.path.join(BASE_DIR, "settings.json")
SERVERS_F   = os.path.join(BASE_DIR, "servers.json")

CONTENT_DIRS = {
    "mod":          os.path.join(MC_DIR, "mods"),
    "resourcepack": os.path.join(MC_DIR, "resourcepacks"),
    "shader":       os.path.join(MC_DIR, "shaderpacks"),
    "datapack":     os.path.join(MC_DIR, "datapacks"),
    "modpack":      os.path.join(MC_DIR, "modpacks"),
}
for _d in [MC_DIR, SERVERS_DIR] + list(CONTENT_DIRS.values()):
    os.makedirs(_d, exist_ok=True)

# ─── Version & update ─────────────────────────────────────────────────────────
APP_VERSION   = "1.0.0"
GITHUB_REPO   = "slava240/minilauncher"
GITHUB_API    = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

def _ver_tuple(s):
    try:
        return tuple(int(x) for x in str(s).lstrip("v").split("."))
    except Exception:
        return (0,)

def check_for_update():
    """Returns (latest_tag, release_url, body) or None."""
    try:
        data = http_get(GITHUB_API, timeout=8)
        tag  = data.get("tag_name", "")
        url  = data.get("html_url", GITHUB_RELEASE_URL)
        body = data.get("body", "")
        if _ver_tuple(tag) > _ver_tuple(APP_VERSION):
            return tag, url, body
    except Exception:
        pass
    return None

# ─── Settings ─────────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "username":        "Player",
    "ram":             2048,
    "last_version":    "",
    "theme":           "dark",
    "language":        "en",
    "jvm_args":        "-XX:+UseG1GC -XX:MaxGCPauseMillis=50",
    "modrinth_server": "original",
    "check_updates":   True,
}

MODRINTH_API = {
    "original":  "https://api.modrinth.com/v2",
    "mirror_rf": "https://modrinth.black/v2",
}

def load_settings():
    if os.path.exists(SETTINGS_F):
        try:
            with open(SETTINGS_F, "r", encoding="utf-8") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    with open(SETTINGS_F, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)

def load_servers():
    if os.path.exists(SERVERS_F):
        try:
            with open(SERVERS_F, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_servers(servers):
    with open(SERVERS_F, "w", encoding="utf-8") as f:
        json.dump(servers, f, indent=2, ensure_ascii=False)

# ─── i18n ─────────────────────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "app_title":         "MiniLauncher",
        "nav_play":          "▶  Play",
        "nav_servers":       "🖥  Servers",
        "nav_modrinth":      "🌿  Modrinth",
        "nav_settings":      "⚙  Settings",
        "theme_toggle":      "🌙 / ☀  Theme",
        "play_title":        "Launch Game",
        "mc_version":        "Minecraft version",
        "releases":          "Releases",
        "snapshots":         "Snapshots",
        "btn_install":       "⬇  Install",
        "btn_launch":        "▶  Launch",
        "installed_vers":    "Installed versions",
        "log_title":         "Log",
        "servers_title":     "Local Servers",
        "btn_create_server": "＋  Create Server",
        "no_servers":        "No servers yet. Click «Create Server».",
        "btn_start":         "▶ Start",
        "btn_stop":          "⏹ Stop",
        "btn_console":       "Console",
        "btn_plugins":       "Plugins",
        "btn_delete":        "Delete",
        "modrinth_title":    "🌿 Modrinth",
        "search_hint":       "Search...",
        "btn_search":        "Search",
        "type_all":          "All types",
        "type_mod":          "Mods",
        "type_rp":           "Resource Packs",
        "type_shader":       "Shaders",
        "type_dp":           "Datapacks",
        "type_mp":           "Modpacks",
        "loader_label":      "  Loader:",
        "status_hint":       "Enter query and press Search",
        "settings_title":    "Settings",
        "username_lbl":      "Player name:",
        "ram_lbl":           "RAM (client):",
        "jvm_lbl":           "JVM args:",
        "modrinth_server_lbl": "Modrinth server",
        "mr_original":       "Original",
        "mr_mirror":         "Mirror (RU)",
        "mc_folder":         "Minecraft folder:",
        "srv_folder":        "Servers folder:",
        "btn_save":          "💾  Save settings",
        "lang_lbl":          "Language:",
        "update_check_lbl":  "Check for updates:",
        "saved_ok":          "Settings saved!",
        "restart_theme":     "Theme changed!\nRestart the launcher to apply.",
        "restart_lang":      "Language changed!\nRestart the launcher to apply.",
        "choose_ver":        "Choose version",
        "btn_download":      "⬇  Download",
        "btn_cancel":        "Cancel",
        "downloaded_title":  "Downloaded!",
        "no_files":          "No files available",
        "err_title":         "Error",
        "warn_title":        "Warning",
        "select_version":    "Select a version",
        "install_prompt":    "{ver} is not installed. Install now?",
        "java_not_found":    "Java not found!\nInstall Java 21:\nhttps://adoptium.net",
        "game_closed":       "Game closed (code {code})",
        "installing":        "Installing {ver}...",
        "installed_ok":      "✓ {ver} installed!",
        "launching":         "Launching {ver} as {user} ({ram} MB)...",
        "no_jar":            "Server jar not found. Recreate the server.",
        "delete_confirm":    "Delete server «{name}» and all its files?",
        "srv_running":       "Server {name} is running. Type commands below.",
        "srv_stopped":       "Server {name} is not running.",
        "plugins_title":     "Plugins — {name}",
        "plugin_downloaded": "Plugin saved to:\n{path}",
        "new_server":        "New Server",
        "srv_name":          "Name:",
        "srv_core":          "Core:",
        "srv_version":       "Version:",
        "srv_port":          "Port:",
        "srv_ram":           "RAM (MB):",
        "btn_create":        "Create & Download Core",
        "folder_created":    "Folder created. Downloading {core} {ver}...",
        "srv_ready":         "✓ {core} {ver} ready!",
        "name_empty":        "Enter server name",
        "name_exists":       "Server «{name}» already exists",
        "port_ram_invalid":  "Port and RAM must be numbers",
        "update_title":      "Update Available!",
        "update_msg":        "New version {tag} is available!\n\nChanges:\n{body}\n\nOpen release page?",
        "update_no":         "No updates found.",
        "checking_update":   "Checking for updates...",
        "ver_filter_all":    "All",
    },
    "ru": {
        "app_title":         "MiniLauncher",
        "nav_play":          "▶  Играть",
        "nav_servers":       "🖥  Серверы",
        "nav_modrinth":      "🌿  Modrinth",
        "nav_settings":      "⚙  Настройки",
        "theme_toggle":      "🌙 / ☀  Тема",
        "play_title":        "Запуск игры",
        "mc_version":        "Версия Minecraft",
        "releases":          "Релизы",
        "snapshots":         "Снапшоты",
        "btn_install":       "⬇  Установить",
        "btn_launch":        "▶  Запустить",
        "installed_vers":    "Установленные версии",
        "log_title":         "Журнал",
        "servers_title":     "Локальные серверы",
        "btn_create_server": "＋  Создать сервер",
        "no_servers":        "Нет серверов. Нажмите «Создать сервер».",
        "btn_start":         "▶ Старт",
        "btn_stop":          "⏹ Стоп",
        "btn_console":       "Консоль",
        "btn_plugins":       "Плагины",
        "btn_delete":        "Удалить",
        "modrinth_title":    "🌿 Modrinth",
        "search_hint":       "Поиск...",
        "btn_search":        "Найти",
        "type_all":          "Все типы",
        "type_mod":          "Моды",
        "type_rp":           "Ресурспаки",
        "type_shader":       "Шейдеры",
        "type_dp":           "Датапаки",
        "type_mp":           "Модпаки",
        "loader_label":      "  Загрузчик:",
        "status_hint":       "Введите запрос и нажмите Найти",
        "settings_title":    "Настройки",
        "username_lbl":      "Имя игрока:",
        "ram_lbl":           "RAM (клиент):",
        "jvm_lbl":           "JVM аргументы:",
        "modrinth_server_lbl": "Сервер Modrinth",
        "mr_original":       "Оригинальный",
        "mr_mirror":         "Зеркало для РФ",
        "mc_folder":         "Папка Minecraft:",
        "srv_folder":        "Папка серверов:",
        "btn_save":          "💾  Сохранить настройки",
        "lang_lbl":          "Язык:",
        "update_check_lbl":  "Проверять обновления:",
        "saved_ok":          "Настройки сохранены!",
        "restart_theme":     "Тема изменена!\nПерезапустите лаунчер.",
        "restart_lang":      "Язык изменён!\nПерезапустите лаунчер.",
        "choose_ver":        "Выбор версии",
        "btn_download":      "⬇  Скачать",
        "btn_cancel":        "Отмена",
        "downloaded_title":  "Скачано!",
        "no_files":          "Нет доступных файлов",
        "err_title":         "Ошибка",
        "warn_title":        "Предупреждение",
        "select_version":    "Выберите версию",
        "install_prompt":    "{ver} не установлена. Установить сейчас?",
        "java_not_found":    "Java не найдена!\nУстановите Java 21:\nhttps://adoptium.net",
        "game_closed":       "Игра завершена (код {code})",
        "installing":        "Установка {ver}...",
        "installed_ok":      "✓ {ver} установлена!",
        "launching":         "Запуск {ver} как {user} ({ram} МБ)...",
        "no_jar":            "Jar файл не найден. Пересоздайте сервер.",
        "delete_confirm":    "Удалить сервер «{name}» и все его файлы?",
        "srv_running":       "Сервер {name} запущен. Введите команду.",
        "srv_stopped":       "Сервер {name} не запущен.",
        "plugins_title":     "Плагины — {name}",
        "plugin_downloaded": "Плагин сохранён в:\n{path}",
        "new_server":        "Новый сервер",
        "srv_name":          "Название:",
        "srv_core":          "Ядро:",
        "srv_version":       "Версия:",
        "srv_port":          "Порт:",
        "srv_ram":           "RAM (МБ):",
        "btn_create":        "Создать и скачать ядро",
        "folder_created":    "Папка создана. Скачиваю {core} {ver}...",
        "srv_ready":         "✓ {core} {ver} готов к запуску!",
        "name_empty":        "Введите название сервера",
        "name_exists":       "Сервер «{name}» уже существует",
        "port_ram_invalid":  "Порт и RAM должны быть числами",
        "update_title":      "Доступно обновление!",
        "update_msg":        "Доступна новая версия {tag}!\n\nИзменения:\n{body}\n\nОткрыть страницу релиза?",
        "update_no":         "Обновлений не найдено.",
        "checking_update":   "Проверка обновлений...",
        "ver_filter_all":    "Все",
    },
}

# ─── Themes ───────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":     "#1a1a24",
        "bg2":    "#13131a",
        "bg3":    "#22222e",
        "border": "#2e2e40",
        "fg":     "#e0e0f0",
        "fg2":    "#7878a0",
        "acc":    "#5dbb63",
        "acc_h":  "#4ea854",
        "btn_fg": "#ffffff",
        "entry":  "#1e1e2a",
        "sel":    "#2a3a2a",
        "card":   "#1e1e2a",
    },
    "light": {
        "bg":     "#f2f2f6",
        "bg2":    "#ffffff",
        "bg3":    "#e6e6f0",
        "border": "#ccccdd",
        "fg":     "#1a1a2e",
        "fg2":    "#606080",
        "acc":    "#3a9e42",
        "acc_h":  "#2d8835",
        "btn_fg": "#ffffff",
        "entry":  "#ffffff",
        "sel":    "#d0ecd0",
        "card":   "#f8f8fc",
    },
}

# ─── Modrinth content types ───────────────────────────────────────────────────
STRIPE_COLORS = {
    "mod":          "#5dbb63",
    "resourcepack": "#5090e0",
    "shader":       "#e0a830",
    "datapack":     "#c060e0",
    "modpack":      "#e05050",
}
TYPE_LABELS_EN = {
    "mod": "MOD", "resourcepack": "RESOURCE PACK",
    "shader": "SHADER", "datapack": "DATAPACK", "modpack": "MODPACK",
}
TYPE_LABELS_RU = {
    "mod": "МОД", "resourcepack": "РЕСУРСПАК",
    "shader": "ШЕЙДЕР", "datapack": "ДАТАПАК", "modpack": "МОДПАК",
}

STATUS_COLORS = {
    "offline":   "#e05050",
    "online":    "#5dbb63",
    "starting":  "#e0a830",
    "stopping":  "#e07040",
}

# ─── Server cores ─────────────────────────────────────────────────────────────
# Common MC versions list used by all cores
ALL_MC_VERSIONS = [
    "1.21.4","1.21.3","1.21.1","1.21",
    "1.20.6","1.20.4","1.20.2","1.20.1","1.20",
    "1.19.4","1.19.3","1.19.2","1.19.1","1.19",
    "1.18.2","1.18.1","1.18",
    "1.17.1","1.17",
    "1.16.5","1.16.4","1.16.3","1.16.2","1.16.1",
    "1.15.2","1.15.1","1.15",
    "1.14.4","1.14.3","1.14.2","1.14.1","1.14",
    "1.13.2","1.13.1","1.13",
    "1.12.2","1.12.1","1.12",
    "1.11.2","1.11",
    "1.10.2","1.10",
    "1.9.4","1.9",
    "1.8.9","1.8.8","1.8",
]

SERVER_CORES = {
    # ── PaperMC family ──────────────────────────────────────────────────────
    "Paper": {
        "desc_en": "High-performance Spigot fork. Recommended for most servers.",
        "desc_ru": "Высокопроизводительный форк Spigot. Рекомендуется.",
        "color":   "#3a8fd9",
        "versions": ["1.21.4","1.21.3","1.21.1","1.20.6","1.20.4","1.20.2",
                     "1.20.1","1.19.4","1.19.3","1.19.2","1.18.2","1.17.1",
                     "1.16.5","1.15.2","1.14.4","1.13.2","1.12.2"],
    },
    "Purpur": {
        "desc_en": "Paper fork with extra gameplay config options.",
        "desc_ru": "Форк Paper с расширенными настройками игрового процесса.",
        "color":   "#9b59b6",
        "versions": ["1.21.4","1.21.3","1.21.1","1.20.6","1.20.4","1.20.1",
                     "1.19.4","1.18.2","1.17.1","1.16.5"],
    },
    "Pufferfish": {
        "desc_en": "Optimized Paper fork focused on performance for large servers.",
        "desc_ru": "Оптимизированный форк Paper для больших серверов.",
        "color":   "#e07830",
        "versions": ["1.21.4","1.21.1","1.20.4","1.20.1","1.19.4","1.18.2"],
    },
    "Folia": {
        "desc_en": "Paper fork with regionized multithreading for large servers.",
        "desc_ru": "Форк Paper с многопоточностью по регионам (для больших серверов).",
        "color":   "#20a0a0",
        "versions": ["1.21.4","1.21.1","1.20.4","1.20.1"],
    },
    # ── Spigot family ───────────────────────────────────────────────────────
    "Spigot": {
        "desc_en": "Classic Spigot server. Plugin-compatible.",
        "desc_ru": "Классический Spigot. Совместим с большинством плагинов.",
        "color":   "#e0a020",
        "versions": ["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1",
                     "1.19.4","1.18.2","1.17.1","1.16.5","1.15.2",
                     "1.14.4","1.12.2","1.8.9"],
    },
    "CraftBukkit": {
        "desc_en": "The original Bukkit server (Spigot build).",
        "desc_ru": "Оригинальный CraftBukkit (сборка Spigot).",
        "color":   "#c08020",
        "versions": ["1.21.4","1.20.1","1.19.4","1.18.2","1.16.5","1.12.2","1.8.9"],
    },
    # ── Mod loaders ─────────────────────────────────────────────────────────
    "Fabric": {
        "desc_en": "Lightweight mod loader server. Great for client mods.",
        "desc_ru": "Лёгкий сервер на Fabric. Отлично для клиентских модов.",
        "color":   "#d4a017",
        "versions": ["1.21.4","1.21.3","1.21.1","1.21","1.20.6","1.20.4",
                     "1.20.2","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5"],
    },
    "Forge": {
        "desc_en": "Forge mod loader server. Required for most Forge mods.",
        "desc_ru": "Сервер с загрузчиком Forge. Нужен для большинства Forge-модов.",
        "color":   "#8060c0",
        "versions": ["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1",
                     "1.19.4","1.18.2","1.17.1","1.16.5","1.15.2",
                     "1.14.4","1.12.2","1.7.10"],
    },
    "NeoForge": {
        "desc_en": "Community fork of Forge with modern improvements.",
        "desc_ru": "Форк Forge с улучшениями от сообщества.",
        "color":   "#e05820",
        "versions": ["1.21.4","1.21.3","1.21.1","1.21","1.20.6","1.20.4","1.20.2","1.20.1"],
    },
    "Quilt": {
        "desc_en": "Fork of Fabric with additional modding features.",
        "desc_ru": "Форк Fabric с дополнительными возможностями для моддинга.",
        "color":   "#7040c0",
        "versions": ["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.18.2"],
    },
    # ── Hybrid (plugins + mods) ─────────────────────────────────────────────
    "Mohist": {
        "desc_en": "Hybrid: Forge mods + Bukkit/Spigot plugins on one server.",
        "desc_ru": "Гибрид: Forge-моды + Bukkit/Spigot-плагины на одном сервере.",
        "color":   "#d04060",
        "versions": ["1.21.1","1.20.1","1.19.4","1.18.2","1.16.5","1.12.2"],
    },
    "Arclight": {
        "desc_en": "Hybrid: Forge + Paper plugins. Stable hybrid option.",
        "desc_ru": "Гибрид: Forge + Paper-плагины. Стабильный гибридный вариант.",
        "color":   "#c030a0",
        "versions": ["1.21.1","1.20.1","1.19.4","1.18.2","1.16.5"],
    },
    "Ketting": {
        "desc_en": "Hybrid: NeoForge/Forge + Paper. Actively developed.",
        "desc_ru": "Гибрид: NeoForge/Forge + Paper. Активно развивается.",
        "color":   "#a050e0",
        "versions": ["1.21.1","1.20.4","1.20.1"],
    },
    # ── Proxy ───────────────────────────────────────────────────────────────
    "Velocity": {
        "desc_en": "Modern high-performance proxy server (replaces BungeeCord).",
        "desc_ru": "Современный высокопроизводительный прокси (замена BungeeCord).",
        "color":   "#20b0e0",
        "versions": ["latest"],
    },
    "BungeeCord": {
        "desc_en": "Classic proxy server for multi-server networks.",
        "desc_ru": "Классический прокси для мультисерверных сетей.",
        "color":   "#60a0e0",
        "versions": ["latest"],
    },
    "Waterfall": {
        "desc_en": "PaperMC fork of BungeeCord with extra features.",
        "desc_ru": "Форк BungeeCord от PaperMC с улучшениями.",
        "color":   "#4080d0",
        "versions": ["latest"],
    },
    # ── Vanilla ─────────────────────────────────────────────────────────────
    "Vanilla": {
        "desc_en": "Official Mojang server. No plugins or mods.",
        "desc_ru": "Официальный сервер Mojang без плагинов и модов.",
        "color":   "#5dbb63",
        "versions": ["1.21.4","1.21.3","1.21.1","1.20.6","1.20.4","1.20.1",
                     "1.19.4","1.18.2","1.17.1","1.16.5","1.15.2",
                     "1.14.4","1.13.2","1.12.2"],
    },
    "Geyser": {
        "desc_en": "Bedrock → Java bridge. Allows Bedrock clients to join Java servers.",
        "desc_ru": "Мост Bedrock → Java. Позволяет Bedrock-клиентам подключаться к Java-серверам.",
        "color":   "#30b080",
        "versions": ["latest"],
    },
}

# Cores that have a real API downloader
DOWNLOADABLE_CORES = {
    "Paper", "Purpur", "Velocity", "Waterfall", "Fabric", "Vanilla", "BungeeCord"
}

# ─────────────────────────────────────────────────────────────────────────────
#  Application
# ─────────────────────────────────────────────────────────────────────────────
class MiniLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings            = load_settings()
        self.t                   = THEMES[self.settings["theme"]]
        self._lang               = self.settings.get("language", "en")
        self.mc_versions         = []
        self.installed_versions  = []
        self.servers             = load_servers()
        self.server_processes    = {}   # name → Popen

        self.title(f"MiniLauncher  v{APP_VERSION}")
        self.geometry("960x610")
        self.minsize(800, 520)
        self.configure(bg=self.t["bg2"])
        self.resizable(True, True)

        self._build_ui()
        self._load_versions_async()

        # Check for updates in background
        if self.settings.get("check_updates", True):
            threading.Thread(target=self._bg_update_check, daemon=True).start()

    def _(self, key, **kw):
        """Translate a string key using current language."""
        lang = self._lang if self._lang in STRINGS else "en"
        s = STRINGS[lang].get(key, STRINGS["en"].get(key, key))
        return s.format(**kw) if kw else s

    # ══════════════════════════════════════════════════════════════════════════
    #  Sidebar + layout
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        t = self.t

        self.sidebar = tk.Frame(self, bg=t["bg2"], width=162)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo + version
        logo_f = tk.Frame(self.sidebar, bg=t["bg2"])
        logo_f.pack(fill="x", padx=14, pady=(14, 2))
        tk.Label(logo_f, text="⛏ MiniLauncher",
                 bg=t["bg2"], fg=t["acc"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(logo_f, text=f"v{APP_VERSION}",
                 bg=t["bg2"], fg=t["fg2"],
                 font=("Segoe UI", 8)).pack(anchor="w")

        tk.Frame(self.sidebar, bg=t["border"], height=1).pack(fill="x", padx=8, pady=(6, 4))

        self.nav_btns = {}
        for key, lkey in [("play",     "nav_play"),
                           ("servers",  "nav_servers"),
                           ("modrinth", "nav_modrinth"),
                           ("settings", "nav_settings")]:
            btn = tk.Button(
                self.sidebar, text=self._(lkey), anchor="w",
                bg=t["bg2"], fg=t["fg2"], relief="flat",
                font=("Segoe UI", 10), padx=14, pady=9,
                cursor="hand2", bd=0,
                activebackground=t["bg3"], activeforeground=t["fg"],
                command=lambda k=key: self._show_tab(k),
            )
            btn.pack(fill="x", padx=6, pady=2)
            self.nav_btns[key] = btn

        # Bottom: update button (hidden until update found) + theme
        tk.Frame(self.sidebar, bg=t["border"], height=1).pack(
            fill="x", padx=8, side="bottom", pady=(0, 4))
        tk.Button(
            self.sidebar, text=self._("theme_toggle"),
            bg=t["bg2"], fg=t["fg2"], relief="flat",
            font=("Segoe UI", 9), padx=14, pady=6,
            cursor="hand2", bd=0, activebackground=t["bg3"],
            command=self._toggle_theme, anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 6), side="bottom")

        self.update_btn = tk.Button(
            self.sidebar, text="🔔  Update available!",
            bg="#e0a020", fg="#1a1000", relief="flat",
            font=("Segoe UI", 9, "bold"), padx=14, pady=6,
            cursor="hand2", bd=0,
            activebackground="#c08010",
            command=self._open_update_page,
            anchor="w",
        )
        # shown only when update found

        self.content = tk.Frame(self, bg=t["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {
            "play":     self._build_play_page(),
            "servers":  self._build_servers_page(),
            "modrinth": self._build_modrinth_page(),
            "settings": self._build_settings_page(),
        }
        self._show_tab("play")

    def _show_tab(self, key):
        t = self.t
        for frame in self.pages.values():
            frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(bg=t["bg3"], fg=t["acc"],
                               font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=t["bg2"], fg=t["fg2"],
                               font=("Segoe UI", 10))
        if key == "servers":
            self._srv_refresh_list()

    # ══════════════════════════════════════════════════════════════════════════
    #  Auto-update check
    # ══════════════════════════════════════════════════════════════════════════
    def _bg_update_check(self):
        result = check_for_update()
        if result:
            tag, url, body = result
            self._update_tag = tag
            self._update_url = url
            self._update_body = body
            self.after(0, self._show_update_banner)

    def _show_update_banner(self):
        self.update_btn.pack(fill="x", padx=6, pady=(0, 4), side="bottom",
                             before=self.sidebar.winfo_children()[-2])

    def _open_update_page(self):
        tag  = getattr(self, "_update_tag", "")
        url  = getattr(self, "_update_url", GITHUB_RELEASE_URL)
        body = getattr(self, "_update_body", "")
        msg  = self._("update_msg", tag=tag,
                       body=body[:400] + ("…" if len(body) > 400 else ""))
        if messagebox.askyesno(self._("update_title"), msg):
            webbrowser.open(url)

    def _manual_update_check(self):
        self._set_update_status(self._("checking_update"))
        def _do():
            result = check_for_update()
            if result:
                tag, url, body = result
                self._update_tag  = tag
                self._update_url  = url
                self._update_body = body
                self.after(0, self._show_update_banner)
                self.after(0, self._open_update_page)
            else:
                self.after(0, lambda: self._set_update_status(self._("update_no")))
        threading.Thread(target=_do, daemon=True).start()

    def _set_update_status(self, msg):
        try:
            self.update_status_lbl.configure(text=msg)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  Play page
    # ══════════════════════════════════════════════════════════════════════════
    def _build_play_page(self):
        t = self.t
        frame = tk.Frame(self.content, bg=t["bg"])

        hdr = tk.Frame(frame, bg=t["bg2"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self._("play_title"), bg=t["bg2"], fg=t["fg"],
                 font=("Segoe UI", 14, "bold"), padx=20).pack(side="left")

        inner = tk.Frame(frame, bg=t["bg"], padx=20, pady=14)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=self._("mc_version"), bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(anchor="w")

        ver_row = tk.Frame(inner, bg=t["bg"])
        ver_row.pack(fill="x", pady=4)
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            ver_row, textvariable=self.version_var,
            font=("Segoe UI", 11), state="readonly", width=22)
        self.version_combo.pack(side="left")

        self.ver_type_var = tk.StringVar(value="release")
        tk.Radiobutton(ver_row, text=self._("releases"),
                       variable=self.ver_type_var, value="release",
                       bg=t["bg"], fg=t["fg"], selectcolor=t["bg3"],
                       activebackground=t["bg"],
                       command=self._filter_versions).pack(side="left", padx=(10,2))
        tk.Radiobutton(ver_row, text=self._("snapshots"),
                       variable=self.ver_type_var, value="snapshot",
                       bg=t["bg"], fg=t["fg"], selectcolor=t["bg3"],
                       activebackground=t["bg"],
                       command=self._filter_versions).pack(side="left")

        btn_row = tk.Frame(inner, bg=t["bg"])
        btn_row.pack(fill="x", pady=(6, 0))
        self._btn(btn_row, self._("btn_install"), self._install_version,
                  style="ghost").pack(side="left")
        self._btn(btn_row, self._("btn_launch"), self._launch_game,
                  style="acc").pack(side="left", padx=(8, 0))

        tk.Label(inner, text=self._("installed_vers"), bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(12, 4))
        self.installed_listbox = tk.Listbox(
            inner, height=4,
            bg=t["bg3"], fg=t["fg"], relief="flat", bd=0,
            font=("Segoe UI", 10), selectbackground=t["sel"],
            selectforeground=t["fg"], activestyle="none",
            highlightthickness=1, highlightbackground=t["border"])
        self.installed_listbox.pack(fill="x")
        self.installed_listbox.bind("<<ListboxSelect>>", self._on_installed_select)

        tk.Label(inner, text=self._("log_title"), bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 4))
        self.log_text = scrolledtext.ScrolledText(
            inner, height=7,
            bg=t["bg2"], fg=t["fg"],
            font=("Consolas", 9), relief="flat", bd=0,
            state="disabled", wrap="word",
            highlightthickness=1, highlightbackground=t["border"])
        self.log_text.pack(fill="both", expand=True)

        self.progress_var   = tk.DoubleVar()
        self.progress_label = tk.Label(inner, text="", bg=t["bg"], fg=t["fg2"],
                                       font=("Segoe UI", 9))
        self.progress_label.pack(anchor="w", pady=(6, 2))
        sty = ttk.Style()
        sty.theme_use("default")
        sty.configure("G.Horizontal.TProgressbar",
                      troughcolor=t["bg3"], background=t["acc"], thickness=5)
        self.progress_bar = ttk.Progressbar(
            inner, variable=self.progress_var, maximum=100,
            style="G.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x")

        return frame

    # ══════════════════════════════════════════════════════════════════════════
    #  Servers page
    # ══════════════════════════════════════════════════════════════════════════
    def _build_servers_page(self):
        t = self.t
        frame = tk.Frame(self.content, bg=t["bg"])

        hdr = tk.Frame(frame, bg=t["bg2"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self._("servers_title"), bg=t["bg2"], fg=t["fg"],
                 font=("Segoe UI", 14, "bold"), padx=20).pack(side="left")

        list_wrap = tk.Frame(frame, bg=t["bg"])
        list_wrap.pack(fill="both", expand=True)

        self.srv_canvas = tk.Canvas(list_wrap, bg=t["bg"], highlightthickness=0)
        srv_vscr = tk.Scrollbar(list_wrap, orient="vertical",
                                command=self.srv_canvas.yview)
        self.srv_canvas.configure(yscrollcommand=srv_vscr.set)
        self.srv_canvas.pack(side="left", fill="both", expand=True)
        srv_vscr.pack(side="right", fill="y")

        self.srv_list_frame = tk.Frame(self.srv_canvas, bg=t["bg"])
        self._srv_win_id = self.srv_canvas.create_window(
            (0, 0), window=self.srv_list_frame, anchor="nw")
        self.srv_list_frame.bind("<Configure>",
            lambda e: self.srv_canvas.configure(
                scrollregion=self.srv_canvas.bbox("all")))
        self.srv_canvas.bind("<Configure>",
            lambda e: self.srv_canvas.itemconfig(self._srv_win_id, width=e.width))
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.srv_canvas.bind(ev, self._srv_scroll)

        bottom = tk.Frame(frame, bg=t["bg2"], pady=10)
        bottom.pack(fill="x", side="bottom")
        self._btn(bottom, self._("btn_create_server"),
                  self._srv_create_dialog, style="acc").pack()

        return frame

    def _srv_scroll(self, e):
        if e.num == 4:   self.srv_canvas.yview_scroll(-1, "units")
        elif e.num == 5: self.srv_canvas.yview_scroll(1, "units")
        else:            self.srv_canvas.yview_scroll(-1*(e.delta//120), "units")

    def _srv_refresh_list(self):
        t = self.t
        for w in self.srv_list_frame.winfo_children():
            w.destroy()
        if not self.servers:
            tk.Label(self.srv_list_frame,
                     text=self._("no_servers"),
                     bg=t["bg"], fg=t["fg2"],
                     font=("Segoe UI", 11), pady=40).pack()
            return
        for srv in self.servers:
            self._srv_add_card(srv)

    def _srv_add_card(self, srv):
        t      = self.t
        name   = srv.get("name", "Server")
        core   = srv.get("core", "Paper")
        ver    = srv.get("version", "?")
        port   = srv.get("port", 25565)
        status = self._srv_get_status(name)
        sc     = STATUS_COLORS.get(status, "#888888")
        cc     = SERVER_CORES.get(core, {}).get("color", "#888888")

        # Status display text
        status_text = {
            "offline": "offline", "online": "online",
            "starting": "starting…", "stopping": "stopping…"
        }.get(status, status)

        card = tk.Frame(self.srv_list_frame, bg=t["card"],
                        highlightbackground=t["border"], highlightthickness=1)
        card.pack(fill="x", pady=4, padx=12)

        tk.Frame(card, bg=sc, width=5).pack(side="left", fill="y")

        info = tk.Frame(card, bg=t["card"])
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        r1 = tk.Frame(info, bg=t["card"])
        r1.pack(anchor="w", fill="x")
        tk.Label(r1, text=name, bg=t["card"], fg=t["fg"],
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(r1, text=f"  {status_text}", bg=t["card"], fg=sc,
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        r2 = tk.Frame(info, bg=t["card"])
        r2.pack(anchor="w", pady=(3, 0))
        tk.Label(r2, text=core, bg=t["card"], fg=cc,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(r2, text=f"  {ver}  •  port {port}",
                 bg=t["card"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        btns = tk.Frame(card, bg=t["card"])
        btns.pack(side="right", padx=10, pady=8)

        if status == "online":
            self._btn(btns, self._("btn_stop"),
                      lambda n=name: self._srv_stop(n),
                      style="ghost").pack(fill="x", pady=2)
        else:
            self._btn(btns, self._("btn_start"),
                      lambda n=name: self._srv_start(n),
                      style="acc").pack(fill="x", pady=2)

        self._btn(btns, self._("btn_console"),
                  lambda n=name: self._srv_open_console(n),
                  style="ghost").pack(fill="x", pady=2)
        self._btn(btns, self._("btn_plugins"),
                  lambda n=name: self._srv_open_plugins(n),
                  style="ghost").pack(fill="x", pady=2)
        self._btn(btns, self._("btn_delete"),
                  lambda n=name: self._srv_delete(n),
                  style="ghost").pack(fill="x", pady=2)

    def _srv_get_status(self, name):
        proc = self.server_processes.get(name)
        if proc is None:  return "offline"
        if proc.poll() is None: return "online"
        return "offline"

    # ── Create server dialog ──────────────────────────────────────────────────
    def _srv_create_dialog(self):
        t   = self.t
        win = tk.Toplevel(self)
        win.title(self._("new_server"))
        win.geometry("520x500")
        win.configure(bg=t["bg"])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=self._("new_server"), bg=t["bg"], fg=t["fg"],
                 font=("Segoe UI", 13, "bold"), pady=12).pack()

        form = tk.Frame(win, bg=t["bg"], padx=24)
        form.pack(fill="x")

        def frow(label_key, widget_fn):
            r = tk.Frame(form, bg=t["bg"])
            r.pack(fill="x", pady=4)
            tk.Label(r, text=self._(label_key), bg=t["bg"], fg=t["fg2"],
                     font=("Segoe UI", 9), width=14, anchor="w").pack(side="left")
            widget_fn(r).pack(side="left", fill="x", expand=True)

        name_var = tk.StringVar(value="My Server")
        frow("srv_name", lambda p: tk.Entry(
            p, textvariable=name_var,
            bg=t["entry"], fg=t["fg"], insertbackground=t["fg"],
            font=("Segoe UI", 10), relief="flat", bd=0,
            highlightbackground=t["border"], highlightthickness=1))

        # Core selector with categories
        core_names = list(SERVER_CORES.keys())
        core_var = tk.StringVar(value="Paper")
        frow("srv_core", lambda p: ttk.Combobox(
            p, textvariable=core_var, values=core_names,
            state="readonly", font=("Segoe UI", 10), width=18))

        ver_var          = tk.StringVar(value="1.21.4")
        ver_combo_holder = [None]
        def mk_ver(p):
            cb = ttk.Combobox(p, textvariable=ver_var,
                              values=SERVER_CORES["Paper"]["versions"],
                              state="readonly", font=("Segoe UI", 10), width=18)
            ver_combo_holder[0] = cb
            return cb
        frow("srv_version", mk_ver)

        def on_core_change(*_):
            c    = core_var.get()
            vers = SERVER_CORES.get(c, {}).get("versions", ["latest"])
            if ver_combo_holder[0]:
                ver_combo_holder[0]["values"] = vers
                ver_var.set(vers[0] if vers else "latest")
            # Update desc
            lang_key = "desc_" + (self._lang if self._lang in ("en","ru") else "en")
            desc = SERVER_CORES.get(c, {}).get(lang_key,
                   SERVER_CORES.get(c, {}).get("desc_en", ""))
            cc   = SERVER_CORES.get(c, {}).get("color", t["acc"])
            core_desc_var.set(desc)
            core_color_lbl.configure(fg=cc)
        core_var.trace_add("write", on_core_change)

        port_var = tk.StringVar(value="25565")
        frow("srv_port", lambda p: tk.Entry(
            p, textvariable=port_var,
            bg=t["entry"], fg=t["fg"], insertbackground=t["fg"],
            font=("Segoe UI", 10), relief="flat", bd=0, width=8,
            highlightbackground=t["border"], highlightthickness=1))

        ram_var = tk.StringVar(value="1024")
        frow("srv_ram", lambda p: tk.Entry(
            p, textvariable=ram_var,
            bg=t["entry"], fg=t["fg"], insertbackground=t["fg"],
            font=("Segoe UI", 10), relief="flat", bd=0, width=8,
            highlightbackground=t["border"], highlightthickness=1))

        # Core description label
        lang_key_init = "desc_" + (self._lang if self._lang in ("en","ru") else "en")
        init_desc = SERVER_CORES["Paper"].get(lang_key_init,
                    SERVER_CORES["Paper"].get("desc_en", ""))
        core_desc_var = tk.StringVar(value=init_desc)
        core_color_lbl = tk.Label(form, textvariable=core_desc_var,
                                  bg=t["bg"], fg=SERVER_CORES["Paper"]["color"],
                                  font=("Segoe UI", 9), wraplength=400, justify="left")
        core_color_lbl.pack(anchor="w", pady=(4, 0))

        # Warning for non-downloadable cores
        warn_var = tk.StringVar(value="")
        tk.Label(form, textvariable=warn_var,
                 bg=t["bg"], fg="#e0a020",
                 font=("Segoe UI", 8), wraplength=400, justify="left").pack(anchor="w")

        def on_core_change2(*_):
            c = core_var.get()
            if c not in DOWNLOADABLE_CORES:
                warn_var.set(
                    "⚠ Auto-download not supported for this core. "
                    "Place the server jar manually in the server folder."
                    if self._lang == "en" else
                    "⚠ Автозагрузка не поддерживается для этого ядра. "
                    "Поместите jar вручную в папку сервера.")
            else:
                warn_var.set("")
        core_var.trace_add("write", on_core_change2)

        tk.Frame(win, bg=t["border"], height=1).pack(fill="x", padx=20, pady=10)

        btn_row    = tk.Frame(win, bg=t["bg"])
        btn_row.pack()
        status_lbl = tk.Label(win, text="", bg=t["bg"], fg=t["acc"],
                              font=("Segoe UI", 9))
        status_lbl.pack(pady=4)

        def do_create():
            n    = name_var.get().strip()
            core = core_var.get()
            ver  = ver_var.get()
            if not n:
                messagebox.showwarning(self._("warn_title"), self._("name_empty"))
                return
            if any(s["name"] == n for s in self.servers):
                messagebox.showwarning(self._("warn_title"), self._("name_exists", name=n))
                return
            try:
                port = int(port_var.get().strip())
                ram  = int(ram_var.get().strip())
            except ValueError:
                messagebox.showwarning(self._("warn_title"), self._("port_ram_invalid"))
                return

            srv_dir = os.path.join(SERVERS_DIR, n)
            os.makedirs(srv_dir, exist_ok=True)
            new_srv = {"name": n, "core": core, "version": ver,
                       "port": port, "ram": ram, "dir": srv_dir, "jar": ""}
            self.servers.append(new_srv)
            save_servers(self.servers)

            status_lbl.configure(
                text=self._("folder_created", core=core, ver=ver))
            win.update()

            threading.Thread(target=self._srv_download_core,
                             args=(new_srv, status_lbl, win),
                             daemon=True).start()

        self._btn(btn_row, self._("btn_create"), do_create,
                  style="acc").pack(side="left", padx=4)
        self._btn(btn_row, self._("btn_cancel"), win.destroy,
                  style="ghost").pack(side="left", padx=4)

    # ── Core downloaders ──────────────────────────────────────────────────────
    def _srv_download_core(self, srv, status_lbl, win):
        core    = srv["core"]
        ver     = srv["version"]
        srv_dir = srv["dir"]

        def upd(msg):
            try:
                self.after(0, lambda: status_lbl.configure(text=msg))
            except Exception:
                pass

        try:
            jar_path = ""
            if   core == "Paper":      jar_path = self._dl_paper(ver, srv_dir, upd)
            elif core == "Purpur":     jar_path = self._dl_purpur(ver, srv_dir, upd)
            elif core == "Velocity":   jar_path = self._dl_velocity(srv_dir, upd)
            elif core == "Waterfall":  jar_path = self._dl_waterfall(srv_dir, upd)
            elif core == "BungeeCord": jar_path = self._dl_bungeecord(srv_dir, upd)
            elif core == "Fabric":     jar_path = self._dl_fabric(ver, srv_dir, upd)
            elif core == "Vanilla":    jar_path = self._dl_vanilla(ver, srv_dir, upd)
            else:
                # Non-downloadable: create placeholder
                jar_path = os.path.join(srv_dir, f"{core.lower()}-server.jar")
                upd(f"⚠ Place {core} jar manually at:\n{jar_path}")

            for s in self.servers:
                if s["name"] == srv["name"]:
                    s["jar"] = jar_path
                    break
            save_servers(self.servers)

            # eula.txt
            eula = os.path.join(srv_dir, "eula.txt")
            if not os.path.exists(eula):
                with open(eula, "w") as f:
                    f.write("eula=true\n")

            # server.properties
            props = os.path.join(srv_dir, "server.properties")
            if not os.path.exists(props):
                with open(props, "w") as f:
                    f.write(f"server-port={srv['port']}\n"
                            "online-mode=false\n"
                            "motd=MiniLauncher Server\n")

            upd(self._("srv_ready", core=core, ver=ver))
            self.after(0, self._srv_refresh_list)
            self.after(2500, lambda: self._safe_close(win))

        except Exception as ex:
            upd(f"✗ Error: {ex}")

    def _safe_close(self, win):
        try: win.destroy()
        except Exception: pass

    def _dl_paper(self, ver, srv_dir, upd):
        upd(f"Fetching Paper {ver} builds...")
        builds   = http_get(
            f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds",
            timeout=10)
        latest   = builds["builds"][-1]["build"]
        jar_name = f"paper-{ver}-{latest}.jar"
        url      = (f"https://api.papermc.io/v2/projects/paper/versions/{ver}"
                    f"/builds/{latest}/downloads/{jar_name}")
        dest     = os.path.join(srv_dir, jar_name)
        upd(f"Downloading {jar_name}...")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"Paper {ver}  {int(d/t*100)}%  ({d//1024} KB)"))
        return dest

    def _dl_purpur(self, ver, srv_dir, upd):
        upd(f"Fetching Purpur {ver}...")
        data     = http_get(f"https://api.purpurmc.org/v2/purpur/{ver}", timeout=10)
        build_id = data["builds"]["latest"]
        url      = f"https://api.purpurmc.org/v2/purpur/{ver}/{build_id}/download"
        jar_name = f"purpur-{ver}-{build_id}.jar"
        dest     = os.path.join(srv_dir, jar_name)
        upd(f"Downloading {jar_name}...")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"Purpur {ver}  {int(d/t*100)}%  ({d//1024} KB)"))
        return dest

    def _dl_velocity(self, srv_dir, upd):
        upd("Fetching Velocity builds...")
        builds   = http_get(
            "https://api.papermc.io/v2/projects/velocity/versions/3.3.0-SNAPSHOT/builds",
            timeout=10)
        latest   = builds["builds"][-1]["build"]
        jar_name = f"velocity-3.3.0-SNAPSHOT-{latest}.jar"
        url      = (f"https://api.papermc.io/v2/projects/velocity/versions"
                    f"/3.3.0-SNAPSHOT/builds/{latest}/downloads/{jar_name}")
        dest     = os.path.join(srv_dir, jar_name)
        upd(f"Downloading {jar_name}...")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"Velocity  {int(d/t*100)}%  ({d//1024} KB)"))
        return dest

    def _dl_waterfall(self, srv_dir, upd):
        upd("Fetching Waterfall builds...")
        builds   = http_get(
            "https://api.papermc.io/v2/projects/waterfall/versions/1.21/builds",
            timeout=10)
        latest   = builds["builds"][-1]["build"]
        jar_name = f"waterfall-1.21-{latest}.jar"
        url      = (f"https://api.papermc.io/v2/projects/waterfall/versions"
                    f"/1.21/builds/{latest}/downloads/{jar_name}")
        dest     = os.path.join(srv_dir, jar_name)
        upd(f"Downloading {jar_name}...")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"Waterfall  {int(d/t*100)}%  ({d//1024} KB)"))
        return dest

    def _dl_bungeecord(self, srv_dir, upd):
        upd("Downloading BungeeCord (latest)...")
        url  = "https://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar"
        dest = os.path.join(srv_dir, "BungeeCord.jar")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"BungeeCord  {int(d/t*100) if t else 0}%  ({d//1024} KB)"))
        return dest

    def _dl_fabric(self, ver, srv_dir, upd):
        upd("Fetching Fabric installer info...")
        installers  = http_get("https://meta.fabricmc.net/v2/versions/installer", timeout=10)
        latest_inst = installers[0]["version"]
        loaders     = http_get("https://meta.fabricmc.net/v2/versions/loader", timeout=10)
        latest_load = loaders[0]["version"]
        url  = (f"https://meta.fabricmc.net/v2/versions/loader/{ver}"
                f"/{latest_load}/{latest_inst}/server/jar")
        dest = os.path.join(srv_dir, f"fabric-server-{ver}.jar")
        upd(f"Downloading Fabric server {ver}...")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"Fabric {ver}  {int(d/t*100)}%  ({d//1024} KB)"))
        return dest

    def _dl_vanilla(self, ver, srv_dir, upd):
        upd("Fetching version manifest...")
        manifest = http_get(
            "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",
            timeout=10)
        v_info = next((v for v in manifest["versions"] if v["id"] == ver), None)
        if not v_info:
            raise ValueError(f"Version {ver} not found in manifest")
        ver_data = http_get(v_info["url"], timeout=10)
        url  = ver_data["downloads"]["server"]["url"]
        dest = os.path.join(srv_dir, f"minecraft_server.{ver}.jar")
        upd(f"Downloading vanilla server {ver}...")
        http_download(url, dest,
                      progress_cb=lambda d, t: upd(
                          f"Vanilla {ver}  {int(d/t*100)}%  ({d//1024} KB)"))
        return dest

    # ── Server start / stop ───────────────────────────────────────────────────
    def _srv_start(self, name):
        srv = next((s for s in self.servers if s["name"] == name), None)
        if not srv:
            return
        jar = srv.get("jar", "")
        if not jar or not os.path.exists(jar):
            messagebox.showerror(self._("err_title"), self._("no_jar"))
            return
        ram = srv.get("ram", 1024)
        cmd = ["java", f"-Xmx{ram}M", f"-Xms{min(ram,512)}M",
               "-jar", jar, "nogui"]
        try:
            proc = subprocess.Popen(
                cmd, cwd=srv["dir"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True)
            self.server_processes[name] = proc
            self._srv_refresh_list()
            threading.Thread(target=self._srv_read_log,
                             args=(name, proc), daemon=True).start()
        except FileNotFoundError:
            messagebox.showerror(self._("err_title"), self._("java_not_found"))

    def _srv_stop(self, name):
        proc = self.server_processes.get(name)
        if proc and proc.poll() is None:
            try:
                proc.stdin.write("stop\n")
                proc.stdin.flush()
            except Exception:
                proc.terminate()
        self.after(2000, self._srv_refresh_list)

    def _srv_read_log(self, name, proc):
        for _ in proc.stdout:
            pass
        proc.wait()
        self.after(500, self._srv_refresh_list)

    def _srv_delete(self, name):
        if not messagebox.askyesno(self._("warn_title"),
                                   self._("delete_confirm", name=name)):
            return
        proc = self.server_processes.get(name)
        if proc and proc.poll() is None:
            proc.terminate()
        srv = next((s for s in self.servers if s["name"] == name), None)
        if srv and os.path.exists(srv.get("dir", "")):
            shutil.rmtree(srv["dir"], ignore_errors=True)
        self.servers = [s for s in self.servers if s["name"] != name]
        save_servers(self.servers)
        self._srv_refresh_list()

    # ── Server console ────────────────────────────────────────────────────────
    def _srv_open_console(self, name):
        t    = self.t
        proc = self.server_processes.get(name)
        win  = tk.Toplevel(self)
        win.title(f"Console — {name}")
        win.geometry("680x460")
        win.configure(bg=t["bg"])

        tk.Label(win, text=f"Console: {name}", bg=t["bg"], fg=t["fg"],
                 font=("Segoe UI", 11, "bold"), pady=10).pack()

        log = scrolledtext.ScrolledText(
            win, bg=t["bg2"], fg=t["acc"],
            font=("Consolas", 9), relief="flat", bd=0,
            state="disabled",
            highlightthickness=1, highlightbackground=t["border"])
        log.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        cmd_row = tk.Frame(win, bg=t["bg"], padx=10, pady=6)
        cmd_row.pack(fill="x")
        cmd_var = tk.StringVar()
        cmd_e = tk.Entry(cmd_row, textvariable=cmd_var,
                         bg=t["entry"], fg=t["fg"], insertbackground=t["fg"],
                         font=("Consolas", 10), relief="flat", bd=0,
                         highlightbackground=t["border"], highlightthickness=1)
        cmd_e.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))

        def send_cmd(*_):
            if proc and proc.poll() is None:
                try:
                    proc.stdin.write(cmd_var.get() + "\n")
                    proc.stdin.flush()
                    cmd_var.set("")
                except Exception as ex:
                    self._console_append(log, f"Error: {ex}\n")

        cmd_e.bind("<Return>", send_cmd)
        self._btn(cmd_row, "Send", send_cmd, style="acc").pack(side="left")

        msg = (self._("srv_running", name=name)
               if (proc and proc.poll() is None)
               else self._("srv_stopped", name=name))
        self._console_append(log, msg + "\n")

        if proc and proc.poll() is None:
            def _read():
                for line in proc.stdout:
                    self.after(0, lambda l=line: self._console_append(log, l))
            threading.Thread(target=_read, daemon=True).start()

    def _console_append(self, widget, text):
        try:
            widget.configure(state="normal")
            widget.insert("end", text)
            widget.see("end")
            widget.configure(state="disabled")
        except Exception:
            pass

    # ── Plugins (Modrinth project_type=plugin) ───────────────────────────────
    def _srv_open_plugins(self, name):
        t   = self.t
        srv = next((s for s in self.servers if s["name"] == name), None)
        if not srv:
            return

        win = tk.Toplevel(self)
        win.title(self._("plugins_title", name=name))
        win.geometry("700x520")
        win.configure(bg=t["bg"])

        tk.Label(win, text=self._("plugins_title", name=name),
                 bg=t["bg"], fg=t["fg"],
                 font=("Segoe UI", 12, "bold"), pady=10).pack()

        sf = tk.Frame(win, bg=t["bg"], padx=14)
        sf.pack(fill="x", pady=(0, 6))
        q_var = tk.StringVar()
        qe = tk.Entry(sf, textvariable=q_var,
                      bg=t["entry"], fg=t["fg"], insertbackground=t["fg"],
                      font=("Segoe UI", 11), relief="flat", bd=0,
                      highlightbackground=t["border"], highlightthickness=1)
        qe.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        status_var = tk.StringVar(value="Search plugins on Modrinth")
        tk.Label(sf, textvariable=status_var, bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="right")

        res_canvas = tk.Canvas(win, bg=t["bg"], highlightthickness=0)
        vscr = tk.Scrollbar(win, orient="vertical", command=res_canvas.yview)
        res_canvas.configure(yscrollcommand=vscr.set)
        res_canvas.pack(side="left", fill="both", expand=True, padx=(14, 0))
        vscr.pack(side="right", fill="y", padx=(0, 4))
        res_frame = tk.Frame(res_canvas, bg=t["bg"])
        _wid = res_canvas.create_window((0, 0), window=res_frame, anchor="nw")
        res_frame.bind("<Configure>",
            lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.bind("<Configure>",
            lambda e: res_canvas.itemconfig(_wid, width=e.width))

        plugins_dir = os.path.join(srv["dir"], "plugins")
        os.makedirs(plugins_dir, exist_ok=True)

        def clear():
            for w in res_frame.winfo_children():
                w.destroy()

        def add_card(item):
            slug       = item.get("slug", "")
            pname      = item.get("title", "?")
            desc       = item.get("description", "")[:120]
            downloads  = item.get("downloads", 0)
            project_id = item.get("project_id", slug)
            dl_fmt     = f"{downloads:,}".replace(",", " ")

            card = tk.Frame(res_frame, bg=t["bg3"],
                            highlightbackground=t["border"], highlightthickness=1)
            card.pack(fill="x", pady=3, padx=4)
            tk.Frame(card, bg="#e05060", width=4).pack(side="left", fill="y")
            body = tk.Frame(card, bg=t["bg3"])
            body.pack(side="left", fill="both", expand=True, padx=10, pady=6)
            tk.Label(body, text=pname, bg=t["bg3"], fg=t["fg"],
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Label(body, text=desc, bg=t["bg3"], fg=t["fg2"],
                     font=("Segoe UI", 9), wraplength=430).pack(anchor="w")
            tk.Label(body, text=f"⬇ {dl_fmt}", bg=t["bg3"], fg=t["fg2"],
                     font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
            rb = tk.Frame(card, bg=t["bg3"])
            rb.pack(side="right", padx=8, pady=8)
            self._btn(rb, "⬇ Download",
                      lambda pid=project_id:
                          threading.Thread(target=self._plugin_dl,
                                           args=(pid, plugins_dir, status_var, win),
                                           daemon=True).start(),
                      style="acc").pack()

        def search_worker(q):
            self.after(0, clear)
            self.after(0, lambda: status_var.set("Searching..."))
            server = self.settings.get("modrinth_server", "original")
            api    = MODRINTH_API[server]
            try:
                data = http_get(f"{api}/search", params={
                    "query": q, "limit": 20,
                    "facets": json.dumps([["project_type:plugin"]])
                }, timeout=10)
                hits = data.get("hits", [])
                self.after(0, lambda: status_var.set(f"Found: {len(hits)}"))
                for item in hits:
                    self.after(0, lambda m=item: add_card(m))
            except OSError:
                self.after(0, lambda: status_var.set("No internet connection"))
            except Exception as ex:
                self.after(0, lambda: status_var.set(f"Error: {ex}"))

        qe.bind("<Return>", lambda e: threading.Thread(
            target=search_worker, args=(q_var.get().strip(),), daemon=True).start())
        self._btn(sf, "Search",
                  lambda: threading.Thread(target=search_worker,
                                           args=(q_var.get().strip(),),
                                           daemon=True).start(),
                  style="acc").pack(side="left")

        threading.Thread(target=search_worker, args=("",), daemon=True).start()

    def _plugin_dl(self, project_id, plugins_dir, status_var, win):
        server = self.settings.get("modrinth_server", "original")
        api    = MODRINTH_API[server]
        try:
            self.after(0, lambda: status_var.set("Fetching versions..."))
            versions = http_get(f"{api}/project/{project_id}/version", timeout=10)
            if not versions:
                self.after(0, lambda: status_var.set("No files"))
                return
            chosen  = versions[0]
            files   = chosen.get("files", [])
            target  = next((f for f in files if f.get("primary")), None) or (files[0] if files else None)
            if not target:
                self.after(0, lambda: status_var.set("No downloadable files"))
                return
            url      = target["url"]
            filename = target.get("filename", url.split("/")[-1])
            dest     = os.path.join(plugins_dir, filename)

            def upd(done, total):
                pct = int(done / total * 100)
                self.after(0, lambda: status_var.set(f"⬇ {filename}  {pct}%"))

            http_download(url, dest, progress_cb=upd)
            self.after(0, lambda: status_var.set(f"✓ {filename}"))
            self.after(0, lambda: messagebox.showinfo(
                self._("downloaded_title"),
                self._("plugin_downloaded", path=plugins_dir),
                parent=win))
        except Exception as ex:
            self.after(0, lambda: status_var.set(f"✗ {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    #  Modrinth page
    # ══════════════════════════════════════════════════════════════════════════
    def _build_modrinth_page(self):
        t = self.t
        frame = tk.Frame(self.content, bg=t["bg"])

        top = tk.Frame(frame, bg=t["bg2"], pady=10, padx=14)
        top.pack(fill="x")
        tk.Label(top, text=self._("modrinth_title"), bg=t["bg2"], fg=t["acc"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        sf = tk.Frame(top, bg=t["bg2"])
        sf.pack(side="left", padx=(14, 0), fill="x", expand=True)
        self.mr_query_var = tk.StringVar()
        e = tk.Entry(sf, textvariable=self.mr_query_var,
                     bg=t["entry"], fg=t["fg"], insertbackground=t["fg"],
                     font=("Segoe UI", 11), relief="flat", bd=0,
                     highlightbackground=t["border"], highlightthickness=1)
        e.pack(side="left", ipady=5, padx=(0, 6), fill="x", expand=True)
        e.bind("<Return>", lambda ev: self._mr_search())
        self._btn(sf, self._("btn_search"), self._mr_search, style="acc").pack(side="left")

        fbar = tk.Frame(frame, bg=t["bg3"], pady=6, padx=14)
        fbar.pack(fill="x")
        tk.Label(fbar, text="Type:", bg=t["bg3"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")
        self.mr_type_var  = tk.StringVar(value="")
        self.mr_type_btns = {}
        type_labels = [
            ("",             self._("type_all")),
            ("mod",          self._("type_mod")),
            ("resourcepack", self._("type_rp")),
            ("shader",       self._("type_shader")),
            ("datapack",     self._("type_dp")),
            ("modpack",      self._("type_mp")),
        ]
        for val, lbl in type_labels:
            b = tk.Button(fbar, text=lbl, bg=t["bg3"], fg=t["fg2"],
                          relief="flat", bd=0,
                          font=("Segoe UI", 9), padx=8, pady=3,
                          cursor="hand2", activebackground=t["border"],
                          command=lambda v=val: self._mr_set_type(v))
            b.pack(side="left", padx=2)
            self.mr_type_btns[val] = b
        self._mr_set_type("")

        tk.Label(fbar, text=self._("loader_label"), bg=t["bg3"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(10, 0))
        self.mr_loader_var = tk.StringVar(value="")
        lcb = ttk.Combobox(fbar, textvariable=self.mr_loader_var,
                           values=["", "fabric", "forge", "quilt", "neoforge"],
                           state="readonly", width=10, font=("Segoe UI", 9))
        lcb.pack(side="left", padx=(4, 0))
        lcb.bind("<<ComboboxSelected>>", lambda e: self._mr_search())

        self.mr_status_var = tk.StringVar(value=self._("status_hint"))
        tk.Label(fbar, textvariable=self.mr_status_var,
                 bg=t["bg3"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="right", padx=6)

        wrap = tk.Frame(frame, bg=t["bg"])
        wrap.pack(fill="both", expand=True)
        self.mr_canvas = tk.Canvas(wrap, bg=t["bg"], highlightthickness=0)
        vscr = tk.Scrollbar(wrap, orient="vertical", command=self.mr_canvas.yview)
        self.mr_canvas.configure(yscrollcommand=vscr.set)
        self.mr_canvas.pack(side="left", fill="both", expand=True)
        vscr.pack(side="right", fill="y")
        self.mr_list = tk.Frame(self.mr_canvas, bg=t["bg"])
        self._mr_win_id = self.mr_canvas.create_window(
            (0, 0), window=self.mr_list, anchor="nw")
        self.mr_list.bind("<Configure>",
            lambda e: self.mr_canvas.configure(
                scrollregion=self.mr_canvas.bbox("all")))
        self.mr_canvas.bind("<Configure>",
            lambda e: self.mr_canvas.itemconfig(self._mr_win_id, width=e.width))
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.mr_canvas.bind(ev, self._mr_scroll)

        return frame

    def _mr_scroll(self, e):
        if e.num == 4:   self.mr_canvas.yview_scroll(-1, "units")
        elif e.num == 5: self.mr_canvas.yview_scroll(1, "units")
        else:            self.mr_canvas.yview_scroll(-1*(e.delta//120), "units")

    def _mr_set_type(self, val):
        t = self.t
        self.mr_type_var.set(val)
        for v, btn in self.mr_type_btns.items():
            if v == val:
                btn.configure(bg=t["acc"], fg=t["btn_fg"],
                               font=("Segoe UI", 9, "bold"))
            else:
                btn.configure(bg=t["bg3"], fg=t["fg2"],
                               font=("Segoe UI", 9))

    def _mr_search(self):
        threading.Thread(target=self._mr_search_worker, daemon=True).start()

    def _mr_search_worker(self):
        self.after(0, self._mr_clear)
        self.after(0, lambda: self.mr_status_var.set("Searching..."))
        query  = self.mr_query_var.get().strip()
        ptype  = self.mr_type_var.get()
        loader = self.mr_loader_var.get().strip()
        server = self.settings.get("modrinth_server", "original")
        api    = MODRINTH_API[server]
        facets = []
        if ptype:  facets.append([f"project_type:{ptype}"])
        if loader: facets.append([f"categories:{loader}"])
        params = {"query": query, "limit": 20}
        if facets: params["facets"] = json.dumps(facets)
        try:
            data = http_get(f"{api}/search", params=params, timeout=10)
            hits = data.get("hits", [])
            srv_lbl = "api.modrinth.com" if server == "original" else "modrinth.black"
            self.after(0, lambda: self.mr_status_var.set(
                f"{len(hits)} results  •  {srv_lbl}"))
            for item in hits:
                self.after(0, lambda m=item: self._mr_add_card(m))
        except OSError:
            self.after(0, lambda: self.mr_status_var.set("No internet connection"))
        except Exception as ex:
            self.after(0, lambda: self.mr_status_var.set(f"Error: {ex}"))

    def _mr_clear(self):
        for w in self.mr_list.winfo_children():
            w.destroy()

    def _mr_add_card(self, item):
        t          = self.t
        slug       = item.get("slug", "")
        name       = item.get("title", "?")
        desc       = item.get("description", "")[:150]
        ptype      = item.get("project_type", "mod")
        downloads  = item.get("downloads", 0)
        project_id = item.get("project_id", slug)
        versions   = item.get("versions", [])
        latest     = versions[-1] if versions else "?"
        dl_fmt     = f"{downloads:,}".replace(",", " ")
        stripe     = STRIPE_COLORS.get(ptype, "#888888")
        type_lbl   = (TYPE_LABELS_EN if self._lang == "en" else TYPE_LABELS_RU).get(
                      ptype, ptype.upper())

        card = tk.Frame(self.mr_list, bg=t["bg3"],
                        highlightbackground=t["border"], highlightthickness=1)
        card.pack(fill="x", pady=3, padx=8)
        tk.Frame(card, bg=stripe, width=4).pack(side="left", fill="y")
        body = tk.Frame(card, bg=t["bg3"])
        body.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        tr = tk.Frame(body, bg=t["bg3"])
        tr.pack(anchor="w", fill="x")
        tk.Label(tr, text=name, bg=t["bg3"], fg=t["fg"],
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(tr, text="  " + type_lbl, bg=t["bg3"], fg=stripe,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(body, text=desc, bg=t["bg3"], fg=t["fg2"],
                 font=("Segoe UI", 9), anchor="w", justify="left",
                 wraplength=500).pack(anchor="w", pady=(2, 4))
        tk.Label(body, text=f"⬇ {dl_fmt}  •  latest: {latest}",
                 bg=t["bg3"], fg=t["fg2"], font=("Segoe UI", 8)).pack(anchor="w")
        bf = tk.Frame(card, bg=t["bg3"])
        bf.pack(side="right", padx=10, pady=8)
        self._btn(bf, self._("btn_download"),
                  lambda pid=project_id, pt=ptype:
                      self._mr_pick_version(pid, pt),
                  style="acc").pack()

    def _mr_pick_version(self, project_id, project_type):
        threading.Thread(target=self._mr_fetch_versions,
                         args=(project_id, project_type), daemon=True).start()

    def _mr_fetch_versions(self, project_id, project_type):
        server = self.settings.get("modrinth_server", "original")
        api    = MODRINTH_API[server]
        try:
            versions = http_get(f"{api}/project/{project_id}/version", timeout=10)
        except Exception as ex:
            self.after(0, lambda: messagebox.showerror(self._("err_title"), str(ex)))
            return
        if not versions:
            self.after(0, lambda: messagebox.showinfo("Modrinth", self._("no_files")))
            return
        self.after(0, lambda: self._mr_version_dialog(versions, project_type))

    def _mr_version_dialog(self, versions, project_type):
        t   = self.t
        win = tk.Toplevel(self)
        win.title(self._("choose_ver"))
        win.geometry("500x380")
        win.configure(bg=t["bg"])
        win.grab_set()
        tk.Label(win, text=self._("choose_ver"), bg=t["bg"], fg=t["fg"],
                 font=("Segoe UI", 11, "bold"), pady=12).pack()
        lf = tk.Frame(win, bg=t["bg"])
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        sb = tk.Scrollbar(lf)
        sb.pack(side="right", fill="y")
        lb = tk.Listbox(lf, bg=t["bg3"], fg=t["fg"],
                        font=("Segoe UI", 10), relief="flat", bd=0,
                        selectbackground=t["sel"], selectforeground=t["fg"],
                        activestyle="none",
                        highlightthickness=1, highlightbackground=t["border"],
                        yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.config(command=lb.yview)
        for v in versions:
            vname   = v.get("name", v.get("version_number", "?"))
            mc_v    = ", ".join(v.get("game_versions", [])[:3])
            loaders = ", ".join(v.get("loaders", []))
            lb.insert("end", f"  {vname}  •  MC {mc_v}  •  {loaders}")
        if versions:
            lb.selection_set(0)
        br = tk.Frame(win, bg=t["bg"], pady=8)
        br.pack()

        def do_dl():
            sel = lb.curselection()
            if not sel: return
            chosen  = versions[sel[0]]
            files   = chosen.get("files", [])
            primary = next((f for f in files if f.get("primary")), None)
            target  = primary or (files[0] if files else None)
            if not target:
                messagebox.showwarning("Modrinth", self._("no_files"))
                return
            url      = target["url"]
            filename = target.get("filename", url.split("/")[-1])
            dest_dir = CONTENT_DIRS.get(project_type, CONTENT_DIRS["mod"])
            dest     = os.path.join(dest_dir, filename)
            win.destroy()
            threading.Thread(target=self._mr_download,
                             args=(url, dest, filename), daemon=True).start()

        self._btn(br, self._("btn_download"), do_dl, style="acc").pack(side="left", padx=4)
        self._btn(br, self._("btn_cancel"), win.destroy, style="ghost").pack(side="left", padx=4)

    def _mr_download(self, url, dest, filename):
        def upd(done, total):
            pct = int(done / total * 100)
            self.after(0, lambda: self.mr_status_var.set(
                f"⬇ {filename}  {pct}%  ({done//1024} KB)"))
        try:
            self.after(0, lambda: self.mr_status_var.set(f"Downloading {filename}..."))
            http_download(url, dest, progress_cb=upd)
            self.after(0, lambda: self.mr_status_var.set(f"✓ {filename} saved"))
            self.after(0, lambda: messagebox.showinfo(
                self._("downloaded_title"),
                f"{filename}\n\n{os.path.dirname(dest)}"))
        except Exception as ex:
            self.after(0, lambda: self.mr_status_var.set(f"✗ {ex}"))
            self.after(0, lambda: messagebox.showerror(self._("err_title"), str(ex)))

    # ══════════════════════════════════════════════════════════════════════════
    #  Settings page
    # ══════════════════════════════════════════════════════════════════════════
    def _build_settings_page(self):
        t = self.t
        frame = tk.Frame(self.content, bg=t["bg"])

        hdr = tk.Frame(frame, bg=t["bg2"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self._("settings_title"), bg=t["bg2"], fg=t["fg"],
                 font=("Segoe UI", 14, "bold"), padx=20).pack(side="left")

        inner = tk.Frame(frame, bg=t["bg"], padx=24, pady=18)
        inner.pack(fill="both", expand=True)

        def sep():
            tk.Frame(inner, bg=t["border"], height=1).pack(
                fill="x", pady=(10, 8))

        def row_f():
            r = tk.Frame(inner, bg=t["bg"])
            r.pack(fill="x", pady=4)
            return r

        def lbl(p, text, w=22):
            return tk.Label(p, text=text, bg=t["bg"], fg=t["fg"],
                            font=("Segoe UI", 10), width=w, anchor="w")

        def ent(p, var, w=24, font=("Segoe UI", 10)):
            return tk.Entry(p, textvariable=var,
                            bg=t["entry"], fg=t["fg"],
                            insertbackground=t["fg"],
                            font=font, relief="flat", bd=0, width=w,
                            highlightbackground=t["border"],
                            highlightthickness=1)

        # Username
        r = row_f()
        lbl(r, self._("username_lbl")).pack(side="left")
        self.username_var = tk.StringVar(value=self.settings["username"])
        ent(r, self.username_var).pack(side="left")

        # RAM
        r = row_f()
        lbl(r, self._("ram_lbl")).pack(side="left")
        self.ram_var = tk.IntVar(value=self.settings["ram"])
        self.ram_lbl_w = tk.Label(r, text=f"{self.settings['ram']} MB",
                                  bg=t["bg"], fg=t["acc"],
                                  font=("Segoe UI", 10, "bold"), width=8)
        self.ram_lbl_w.pack(side="right")
        tk.Scale(r, from_=512, to=16384, resolution=512,
                 variable=self.ram_var, orient="horizontal",
                 bg=t["bg"], fg=t["fg"], troughcolor=t["bg3"],
                 highlightthickness=0, relief="flat",
                 showvalue=False, length=200,
                 command=lambda v: self.ram_lbl_w.configure(
                     text=f"{int(float(v))} MB")
                 ).pack(side="left", padx=(0, 6))

        # JVM
        r = row_f()
        lbl(r, self._("jvm_lbl")).pack(side="left")
        self.jvm_var = tk.StringVar(value=self.settings.get("jvm_args", ""))
        ent(r, self.jvm_var, w=30, font=("Consolas", 9)).pack(side="left")

        sep()

        # Language
        r = row_f()
        lbl(r, self._("lang_lbl")).pack(side="left")
        self.lang_var = tk.StringVar(value=self.settings.get("language", "en"))
        for val, display in [("en", "English"), ("ru", "Русский")]:
            tk.Radiobutton(r, text=display, variable=self.lang_var, value=val,
                           bg=t["bg"], fg=t["fg"], selectcolor=t["bg3"],
                           activebackground=t["bg"],
                           font=("Segoe UI", 10)).pack(side="left", padx=(0, 14))

        sep()

        # Modrinth server
        tk.Label(inner, text=self._("modrinth_server_lbl"),
                 bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        self.modrinth_server_var = tk.StringVar(
            value=self.settings.get("modrinth_server", "original"))
        for val, nk, hint in [
            ("original",  "mr_original", "api.modrinth.com"),
            ("mirror_rf", "mr_mirror",   "modrinth.black"),
        ]:
            r = tk.Frame(inner, bg=t["bg"])
            r.pack(anchor="w", pady=2)
            tk.Radiobutton(r, text=self._(nk),
                           variable=self.modrinth_server_var, value=val,
                           bg=t["bg"], fg=t["fg"],
                           selectcolor=t["bg3"], activebackground=t["bg"],
                           font=("Segoe UI", 10)).pack(side="left")
            tk.Label(r, text=hint, bg=t["bg"], fg=t["fg2"],
                     font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

        sep()

        # Update check
        r = row_f()
        lbl(r, self._("update_check_lbl")).pack(side="left")
        self.update_check_var = tk.BooleanVar(
            value=self.settings.get("check_updates", True))
        tk.Checkbutton(r, variable=self.update_check_var,
                       bg=t["bg"], fg=t["fg"],
                       selectcolor=t["bg3"],
                       activebackground=t["bg"]).pack(side="left")

        # Manual check button
        r2 = row_f()
        self._btn(r2, "🔍  Check for updates now",
                  self._manual_update_check, style="ghost").pack(side="left")
        self.update_status_lbl = tk.Label(r2, text="",
                                          bg=t["bg"], fg=t["acc"],
                                          font=("Segoe UI", 9))
        self.update_status_lbl.pack(side="left", padx=10)

        sep()

        # Paths
        r = row_f()
        lbl(r, self._("mc_folder")).pack(side="left")
        tk.Label(r, text=MC_DIR, bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")
        r2 = row_f()
        lbl(r2, self._("srv_folder")).pack(side="left")
        tk.Label(r2, text=SERVERS_DIR, bg=t["bg"], fg=t["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        sep()
        self._btn(inner, self._("btn_save"),
                  self._save_settings, style="acc").pack(anchor="w")

        return frame

    # ══════════════════════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════════════════════
    def _btn(self, parent, text, cmd, style="ghost"):
        t = self.t
        if style == "acc":
            bg, fg, abg = t["acc"], t["btn_fg"], t["acc_h"]
        else:
            bg, fg, abg = t["bg3"], t["fg"], t["border"]
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg, activebackground=abg,
                         activeforeground=fg,
                         font=("Segoe UI", 10, "bold"),
                         relief="flat", bd=0,
                         padx=12, pady=6, cursor="hand2")

    def _log(self, msg):
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.after(0, _do)

    def _set_progress(self, val, label=""):
        self.after(0, lambda: self.progress_var.set(val))
        self.after(0, lambda: self.progress_label.configure(text=label))

    # ══════════════════════════════════════════════════════════════════════════
    #  MC versions
    # ══════════════════════════════════════════════════════════════════════════
    def _load_versions_async(self):
        threading.Thread(target=self._load_versions, daemon=True).start()

    def _load_versions(self):
        self._log("Fetching Minecraft version list...")
        try:
            self.mc_versions = minecraft_launcher_lib.utils.get_version_list()
            self._filter_versions()
            self._refresh_installed()
            self._log(f"Loaded {len(self.mc_versions)} versions")
        except Exception as ex:
            self._log(f"Error: {ex}")

    def _filter_versions(self):
        vtype    = self.ver_type_var.get()
        filtered = [v["id"] for v in self.mc_versions if v["type"] == vtype]
        def _do():
            self.version_combo["values"] = filtered
            if filtered:
                last = self.settings.get("last_version", "")
                self.version_var.set(last if last in filtered else filtered[0])
        self.after(0, _do)

    def _refresh_installed(self):
        try:
            inst = minecraft_launcher_lib.utils.get_installed_versions(MC_DIR)
            self.installed_versions = [v["id"] for v in inst]
        except Exception:
            self.installed_versions = []
        def _do():
            self.installed_listbox.delete(0, "end")
            for v in self.installed_versions:
                self.installed_listbox.insert("end", "  " + v)
            if not self.installed_versions:
                self.installed_listbox.insert("end", "  No installed versions")
        self.after(0, _do)

    def _on_installed_select(self, event):
        sel = self.installed_listbox.curselection()
        if sel and sel[0] < len(self.installed_versions):
            self.version_var.set(self.installed_versions[sel[0]])

    # ══════════════════════════════════════════════════════════════════════════
    #  MC install / launch
    # ══════════════════════════════════════════════════════════════════════════
    def _install_version(self):
        ver = self.version_var.get()
        if not ver:
            messagebox.showwarning(self._("warn_title"), self._("select_version"))
            return
        threading.Thread(target=self._install_worker, args=(ver,), daemon=True).start()

    def _install_worker(self, ver):
        self._log(self._("installing", ver=ver))
        self._set_progress(0, self._("installing", ver=ver))
        callbacks = {
            "setStatus":   lambda s: self._log(f"  {s}"),
            "setProgress": lambda v: None,
            "setMax":      lambda v: None,
        }
        try:
            minecraft_launcher_lib.install.install_minecraft_version(
                ver, MC_DIR, callback=callbacks)
            self._log(self._("installed_ok", ver=ver))
            self._set_progress(100, self._("installed_ok", ver=ver))
            self._refresh_installed()
        except Exception as ex:
            self._log(f"✗ {ex}")
            self._set_progress(0, "Error")

    def _launch_game(self):
        ver = self.version_var.get()
        if not ver:
            messagebox.showwarning(self._("warn_title"), self._("select_version"))
            return
        if ver not in self.installed_versions:
            if messagebox.askyesno("MiniLauncher",
                                   self._("install_prompt", ver=ver)):
                def _i():
                    self._install_worker(ver)
                    self.after(0, self._launch_game)
                threading.Thread(target=_i, daemon=True).start()
            return
        threading.Thread(target=self._launch_worker, args=(ver,), daemon=True).start()

    def _launch_worker(self, ver):
        ram  = self.settings["ram"]
        user = self.settings["username"]
        jvm  = self.settings.get("jvm_args", "")
        self._log(self._("launching", ver=ver, user=user, ram=ram))
        self._set_progress(50, "Preparing...")
        options = {
            "username":    user,
            "uuid":        "00000000-0000-0000-0000-000000000000",
            "token":       "0",
            "jvmArguments": [f"-Xmx{ram}M", f"-Xms{min(ram,512)}M"] + (
                jvm.split() if jvm else []),
        }
        try:
            cmd = minecraft_launcher_lib.command.get_minecraft_command(
                ver, MC_DIR, options)
        except Exception as ex:
            self._log(f"✗ {ex}")
            self._set_progress(0, "")
            return
        self._log("Launching...")
        self._set_progress(100, "Game running!")
        self.settings["last_version"] = ver
        save_settings(self.settings)
        try:
            proc = subprocess.Popen(
                cmd, cwd=MC_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self._log(f"[MC] {line}")
            proc.wait()
            self._log(self._("game_closed", code=proc.returncode))
            self._set_progress(0, "Game closed")
        except FileNotFoundError:
            self._log("✗ Java not found!")
            messagebox.showerror(self._("err_title"), self._("java_not_found"))
            self._set_progress(0, "")
        except Exception as ex:
            self._log(f"✗ {ex}")
            self._set_progress(0, "")

    # ══════════════════════════════════════════════════════════════════════════
    #  Save settings / theme
    # ══════════════════════════════════════════════════════════════════════════
    def _save_settings(self):
        self.settings["username"]        = self.username_var.get().strip() or "Player"
        self.settings["ram"]             = self.ram_var.get()
        self.settings["jvm_args"]        = self.jvm_var.get().strip()
        self.settings["modrinth_server"] = self.modrinth_server_var.get()
        self.settings["check_updates"]   = self.update_check_var.get()
        old_lang = self.settings.get("language", "en")
        new_lang = self.lang_var.get()
        self.settings["language"] = new_lang
        save_settings(self.settings)
        messagebox.showinfo("MiniLauncher", self._("saved_ok"))
        if new_lang != old_lang:
            messagebox.showinfo("MiniLauncher", self._("restart_lang"))

    def _toggle_theme(self):
        self.settings["theme"] = (
            "light" if self.settings["theme"] == "dark" else "dark")
        save_settings(self.settings)
        messagebox.showinfo("MiniLauncher", self._("restart_theme"))


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MiniLauncher()
    app.mainloop()
