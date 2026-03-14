"""
MiniLauncher v1.1.0  –  CustomTkinter edition
pip install minecraft-launcher-lib requests pillow customtkinter
"""
# ─── stdlib ───────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import messagebox, colorchooser
import threading, json, os, sys, subprocess, urllib.request, urllib.parse
import shutil, webbrowser, socket, time, re, hashlib
from io import BytesIO

# ─── CustomTkinter ────────────────────────────────────────────────────────────
import customtkinter as ctk
ctk.set_default_color_theme("dark-blue")

# ─── PIL (optional) ───────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ─── HTTP ─────────────────────────────────────────────────────────────────────
try:
    import requests as _req
    def http_get(url, params=None, timeout=10, headers=None):
        h = {"User-Agent": "MiniLauncher/1.1"}
        if headers: h.update(headers)
        if params:  url += "?" + urllib.parse.urlencode(params)
        r = _req.get(url, headers=h, timeout=timeout); r.raise_for_status(); return r.json()
    def http_get_bytes(url, timeout=10):
        return _req.get(url, headers={"User-Agent":"MiniLauncher/1.1"}, timeout=timeout).content
    def http_post(url, data, timeout=15, headers=None):
        h = {"User-Agent":"MiniLauncher/1.1","Content-Type":"application/json"}
        if headers: h.update(headers)
        r = _req.post(url, json=data, headers=h, timeout=timeout); r.raise_for_status(); return r.json()
    def http_download(url, dest, progress_cb=None):
        with _req.get(url, stream=True, timeout=120, headers={"User-Agent":"MiniLauncher/1.1"}) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0)); done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk); done += len(chunk)
                    if progress_cb and total: progress_cb(done, total)
except ImportError:
    def http_get(url, params=None, timeout=10, headers=None):
        if params: url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent":"MiniLauncher/1.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode())
    def http_get_bytes(url, timeout=10):
        req = urllib.request.Request(url, headers={"User-Agent":"MiniLauncher/1.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()
    def http_post(url, data, timeout=15, headers=None):
        body = json.dumps(data).encode()
        req  = urllib.request.Request(url, data=body, method="POST",
               headers={"Content-Type":"application/json","User-Agent":"MiniLauncher/1.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode())
    def http_download(url, dest, progress_cb=None):
        req = urllib.request.Request(url, headers={"User-Agent":"MiniLauncher/1.1"})
        with urllib.request.urlopen(req, timeout=120) as r:
            total = int(r.headers.get("Content-Length",0)); done = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk: break
                    f.write(chunk); done += len(chunk)
                    if progress_cb and total: progress_cb(done, total)

import minecraft_launcher_lib

# ─── Paths ─────────────────────────────────────────────────────────────────────
if getattr(sys,"frozen",False): BASE_DIR = os.path.dirname(sys.executable)
else:                            BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MC_DIR        = os.path.join(BASE_DIR,"minecraft")
SERVERS_DIR   = os.path.join(BASE_DIR,"servers")
INSTANCES_DIR = os.path.join(BASE_DIR,"instances")
JAVA_DIR      = os.path.join(BASE_DIR,"java")
SETTINGS_F    = os.path.join(BASE_DIR,"settings.json")
SERVERS_F     = os.path.join(BASE_DIR,"servers.json")
ACCOUNTS_F    = os.path.join(BASE_DIR,"accounts.json")
INSTANCES_F   = os.path.join(BASE_DIR,"instances.json")

for _d in [MC_DIR,SERVERS_DIR,INSTANCES_DIR,JAVA_DIR,
           os.path.join(MC_DIR,"mods"),os.path.join(MC_DIR,"resourcepacks"),
           os.path.join(MC_DIR,"shaderpacks"),os.path.join(MC_DIR,"datapacks")]:
    os.makedirs(_d,exist_ok=True)

# ─── Constants ─────────────────────────────────────────────────────────────────
APP_VERSION   = "1.1.0"
GITHUB_REPO   = "slava240/minilauncher"
GITHUB_URL    = f"https://github.com/{GITHUB_REPO}"
GITHUB_API    = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_REL    = f"https://github.com/{GITHUB_REPO}/releases/latest"

MS_CLIENT_ID  = "00000000402b5328"
MS_DEVICE_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
MS_TOKEN_URL  = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
MS_SCOPE      = "XboxLive.signin offline_access"
XBL_URL       = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_URL      = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_AUTH_URL   = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE    = "https://api.minecraftservices.com/minecraft/profile"
ELY_AUTH_URL  = "https://authserver.ely.by/auth/authenticate"
ELY_SKIN_URL  = "https://skinsystem.ely.by/skins/{username}.png"
JAVA_API      = "https://api.adoptium.net/v3/assets/latest/{major}/hotspot?os={os}&arch=x64&image_type=jre"
JAVA_OS_MAP   = {"win32":"windows","linux":"linux","darwin":"mac"}
MODRINTH_API  = {"original":"https://api.modrinth.com/v2","mirror_rf":"https://modrinth.black/v2"}

SERVER_CORES  = {
    "Paper":       {"color":"#3a8fd9","desc":"High-performance Spigot fork. Recommended.",
                    "versions":["1.21.4","1.21.3","1.21.1","1.20.6","1.20.4","1.20.2","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5","1.15.2","1.14.4","1.13.2","1.12.2"]},
    "Purpur":      {"color":"#9b59b6","desc":"Paper fork with extra config options.",
                    "versions":["1.21.4","1.21.3","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5"]},
    "Pufferfish":  {"color":"#e07830","desc":"Optimised Paper fork for large servers.",
                    "versions":["1.21.4","1.21.1","1.20.4","1.20.1","1.19.4","1.18.2"]},
    "Folia":       {"color":"#20a0a0","desc":"Regionized multithreading Paper fork.",
                    "versions":["1.21.4","1.21.1","1.20.4","1.20.1"]},
    "Spigot":      {"color":"#e0a020","desc":"Classic Spigot server.",
                    "versions":["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5","1.12.2","1.8.9"]},
    "CraftBukkit": {"color":"#c08020","desc":"Original Bukkit (Spigot build).",
                    "versions":["1.21.4","1.20.1","1.19.4","1.18.2","1.16.5","1.12.2","1.8.9"]},
    "Fabric":      {"color":"#d4a017","desc":"Lightweight mod-loader server.",
                    "versions":["1.21.4","1.21.3","1.21.1","1.21","1.20.6","1.20.4","1.20.2","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5"]},
    "Forge":       {"color":"#8060c0","desc":"Forge mod-loader server.",
                    "versions":["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5","1.15.2","1.14.4","1.12.2"]},
    "NeoForge":    {"color":"#e05820","desc":"Community Forge fork.",
                    "versions":["1.21.4","1.21.3","1.21.1","1.21","1.20.6","1.20.4","1.20.2","1.20.1"]},
    "Quilt":       {"color":"#7040c0","desc":"Fabric fork with extra features.",
                    "versions":["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.18.2"]},
    "Mohist":      {"color":"#d04060","desc":"Forge + Bukkit/Spigot hybrid.",
                    "versions":["1.21.1","1.20.1","1.19.4","1.18.2","1.16.5","1.12.2"]},
    "Arclight":    {"color":"#c030a0","desc":"Forge + Paper hybrid.",
                    "versions":["1.21.1","1.20.1","1.19.4","1.18.2","1.16.5"]},
    "Ketting":     {"color":"#a050e0","desc":"NeoForge + Paper hybrid.",
                    "versions":["1.21.1","1.20.4","1.20.1"]},
    "Velocity":    {"color":"#20b0e0","desc":"Modern high-performance proxy.",
                    "versions":["latest"]},
    "BungeeCord":  {"color":"#60a0e0","desc":"Classic BungeeCord proxy.",
                    "versions":["latest"]},
    "Waterfall":   {"color":"#4080d0","desc":"PaperMC BungeeCord fork.",
                    "versions":["latest"]},
    "Vanilla":     {"color":"#5dbb63","desc":"Official Mojang server, no plugins.",
                    "versions":["1.21.4","1.21.3","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.18.2","1.17.1","1.16.5","1.15.2","1.14.4","1.13.2","1.12.2"]},
    "Geyser":      {"color":"#30b080","desc":"Bedrock → Java bridge.",
                    "versions":["latest"]},
}
DOWNLOADABLE = {"Paper","Purpur","Velocity","Waterfall","BungeeCord","Fabric","Vanilla"}

STRIPE_C = {"mod":"#5dbb63","resourcepack":"#5090e0","shader":"#e0a830","datapack":"#c060e0","modpack":"#e05050"}

# ─── colour palette per appearance ─────────────────────────────────────────────
def _pal():
    m = ctk.get_appearance_mode()          # "Dark" or "Light"
    if m == "Dark":
        return {"bg":"#1a1a24","bg2":"#13131a","bg3":"#22222e",
                "border":"#2e2e40","fg":"#e0e0f0","fg2":"#7878a0",
                "card":"#1e1e2a","entry":"#1e1e2a","sel":"#2a3a2a"}
    else:
        return {"bg":"#f2f4f8","bg2":"#ffffff","bg3":"#e8eaf0",
                "border":"#d0d4e0","fg":"#1a1a2e","fg2":"#606080",
                "card":"#f8f8fc","entry":"#ffffff","sel":"#d0ecd0"}

# ─── i18n (short version) ──────────────────────────────────────────────────────
T = {
"en":{
    "play":"▶  Play","servers":"🖥  Servers","modrinth":"🌿  Modrinth",
    "settings":"⚙  Settings","nav_lan":"📡  LAN","instances":"🗂  Instances",
    "play_title":"Launch Game","mc_ver":"Minecraft Version",
    "releases":"Releases","snapshots":"Snapshots",
    "btn_install":"⬇  Install","btn_launch":"▶  Launch",
    "installed":"Installed versions","log_lbl":"Log",
    "servers_title":"Local Servers","btn_create_srv":"＋  New Server",
    "no_servers":"No servers yet. Click «New Server».",
    "start":"▶ Start","stop":"⏹ Stop","console":"Console",
    "plugins":"Plugins","delete":"Delete","dashboard":"Dashboard",
    "modrinth_t":"🌿 Modrinth","search":"Search","all_types":"All",
    "mods":"Mods","rp":"Resource Packs","shaders":"Shaders",
    "dp":"Datapacks","mp":"Modpacks","loader_lbl":"Loader:",
    "hint":"Enter query and press Search",
    "settings_t":"Settings","username_l":"Player name:","ram_l":"RAM (client):",
    "jvm_l":"JVM args:","mr_server":"Modrinth Server",
    "mr_orig":"Original","mr_mirror":"Mirror (RU)",
    "save_btn":"💾  Save","lang_l":"Language:",
    "upd_check":"Check updates:","saved":"Settings saved!",
    "restart_t":"Restart to apply theme/language changes.",
    "choose_ver":"Choose version","download":"⬇  Download","cancel":"Cancel",
    "no_files":"No files","err":"Error","warn":"Warning","select_ver":"Select a version",
    "install_q":"{ver} not installed. Install now?",
    "java_err":"Java not found!\nhttps://adoptium.net",
    "closed":"Game closed (code {code})","installing":"Installing {ver}…",
    "inst_ok":"✓ {ver} installed!","launching":"Launching {ver} as {user}…",
    "no_jar":"Server jar not found. Recreate server.",
    "delete_q":"Delete server «{n}» and all files?",
    "srv_on":"Server {n} is running.","srv_off":"Server {n} is not running.",
    "plugins_t":"Plugins — {n}",
    "new_srv":"New Server","srv_name":"Name:","srv_core":"Core:",
    "srv_ver":"Version:","srv_port":"Port:","srv_ram":"RAM (MB):",
    "btn_create":"Create & Download Core","creating":"Downloading {core} {ver}…",
    "srv_ready":"✓ {core} {ver} ready!","name_empty":"Enter a name",
    "name_exists":"«{n}» already exists","port_invalid":"Port and RAM must be numbers",
    "upd_title":"Update Available!",
    "upd_msg":"Version {tag} is available!\n\n{body}\n\nOpen release page?",
    "upd_no":"No updates found.","checking":"Checking…",
    "inst_t":"Instances","new_inst":"New Instance","inst_name":"Name:",
    "inst_ver":"MC Version:","inst_loader":"Loader:","inst_lver":"Loader version:",
    "btn_new_inst":"＋  New Instance","no_inst":"No instances yet.",
    "accounts_t":"Accounts","add_ms":"＋ Microsoft","add_ely":"＋ Ely.By",
    "add_offline":"＋ Offline","no_accounts":"No accounts.",
    "active_lbl":"Set active","remove_acc":"Remove",
    "ms_auth_title":"Microsoft Login",
    "ms_auth_msg":"1. Open: {url}\n2. Enter code: {code}\n\n(Browser opened automatically)",
    "ely_user":"Username:","ely_pass":"Password:","ely_login":"Login",
    "offline_name":"Player name:",
    "java_t":"Java","auto_dl_java":"Auto-download Java 21",
    "java_dl":"Downloading Java {ver}…","java_ok":"✓ Java {ver} installed!",
    "java_check":"Check Java","accent_t":"Accent Color","pick_color":"Pick…",
    "gradient_t":"Animated gradient accent","gradient_en":"Enable gradient",
    "grad_c1":"Color 1:","grad_c2":"Color 2:",
    "lan_t":"LAN Servers","lan_searching":"Scanning LAN…",
    "lan_none":"No LAN servers found.","btn_join":"▶ Join","lan_refresh":"↻ Refresh",
    "dash_t":"Dashboard — {n}","dash_players":"Online players",
    "dash_op":"Give OP","dash_ban":"Ban","dash_kick":"Kick","dash_cpu":"RAM usage",
    "dash_total":"Total joins","send":"Send","inst_label":"Install to instance:",
},
"ru":{
    "play":"▶  Играть","servers":"🖥  Серверы","modrinth":"🌿  Modrinth",
    "settings":"⚙  Настройки","nav_lan":"📡  LAN","instances":"🗂  Сборки",
    "play_title":"Запуск игры","mc_ver":"Версия Minecraft",
    "releases":"Релизы","snapshots":"Снапшоты",
    "btn_install":"⬇  Установить","btn_launch":"▶  Запустить",
    "installed":"Установленные версии","log_lbl":"Журнал",
    "servers_title":"Локальные серверы","btn_create_srv":"＋  Новый сервер",
    "no_servers":"Нет серверов. Нажмите «Новый сервер».",
    "start":"▶ Старт","stop":"⏹ Стоп","console":"Консоль",
    "plugins":"Плагины","delete":"Удалить","dashboard":"Дашборд",
    "modrinth_t":"🌿 Modrinth","search":"Найти","all_types":"Все",
    "mods":"Моды","rp":"Ресурспаки","shaders":"Шейдеры",
    "dp":"Датапаки","mp":"Модпаки","loader_lbl":"Загрузчик:",
    "hint":"Введите запрос и нажмите Найти",
    "settings_t":"Настройки","username_l":"Имя игрока:","ram_l":"RAM (клиент):",
    "jvm_l":"JVM аргументы:","mr_server":"Сервер Modrinth",
    "mr_orig":"Оригинальный","mr_mirror":"Зеркало РФ",
    "save_btn":"💾  Сохранить","lang_l":"Язык:",
    "upd_check":"Проверять обновления:","saved":"Настройки сохранены!",
    "restart_t":"Перезапустите лаунчер для применения изменений.",
    "choose_ver":"Выбор версии","download":"⬇  Скачать","cancel":"Отмена",
    "no_files":"Нет файлов","err":"Ошибка","warn":"Предупреждение",
    "select_ver":"Выберите версию",
    "install_q":"{ver} не установлена. Установить?",
    "java_err":"Java не найдена!\nhttps://adoptium.net",
    "closed":"Игра закрыта (код {code})","installing":"Установка {ver}…",
    "inst_ok":"✓ {ver} установлена!","launching":"Запуск {ver} как {user}…",
    "no_jar":"Jar не найден. Пересоздайте сервер.",
    "delete_q":"Удалить сервер «{n}» и все файлы?",
    "srv_on":"Сервер {n} запущен.","srv_off":"Сервер {n} не запущен.",
    "plugins_t":"Плагины — {n}",
    "new_srv":"Новый сервер","srv_name":"Название:","srv_core":"Ядро:",
    "srv_ver":"Версия:","srv_port":"Порт:","srv_ram":"RAM (МБ):",
    "btn_create":"Создать и скачать ядро","creating":"Скачиваю {core} {ver}…",
    "srv_ready":"✓ {core} {ver} готов!","name_empty":"Введите название",
    "name_exists":"«{n}» уже существует","port_invalid":"Порт и RAM — числа",
    "upd_title":"Доступно обновление!",
    "upd_msg":"Версия {tag} доступна!\n\n{body}\n\nОткрыть страницу?",
    "upd_no":"Обновлений нет.","checking":"Проверяю…",
    "inst_t":"Сборки","new_inst":"Новая сборка","inst_name":"Название:",
    "inst_ver":"Версия MC:","inst_loader":"Загрузчик:","inst_lver":"Версия загрузчика:",
    "btn_new_inst":"＋  Новая сборка","no_inst":"Нет сборок.",
    "accounts_t":"Аккаунты","add_ms":"＋ Microsoft","add_ely":"＋ Ely.By",
    "add_offline":"＋ Оффлайн","no_accounts":"Нет аккаунтов.",
    "active_lbl":"Сделать активным","remove_acc":"Удалить",
    "ms_auth_title":"Вход Microsoft",
    "ms_auth_msg":"1. Откройте: {url}\n2. Введите код: {code}\n\n(Браузер открыт автоматически)",
    "ely_user":"Логин:","ely_pass":"Пароль:","ely_login":"Войти",
    "offline_name":"Имя игрока:",
    "java_t":"Java","auto_dl_java":"Авто-загрузка Java 21",
    "java_dl":"Скачиваю Java {ver}…","java_ok":"✓ Java {ver} установлена!",
    "java_check":"Проверить Java","accent_t":"Цвет акцента","pick_color":"Выбрать…",
    "gradient_t":"Анимированный градиент акцента","gradient_en":"Включить градиент",
    "grad_c1":"Цвет 1:","grad_c2":"Цвет 2:",
    "lan_t":"LAN Серверы","lan_searching":"Поиск LAN серверов…",
    "lan_none":"LAN серверов не найдено.","btn_join":"▶ Войти","lan_refresh":"↻ Обновить",
    "dash_t":"Дашборд — {n}","dash_players":"Игроки онлайн",
    "dash_op":"Дать OP","dash_ban":"Бан","dash_kick":"Кик","dash_cpu":"Потребление RAM",
    "dash_total":"Всего заходов","send":"Отправить","inst_label":"Установить в сборку:",
},
}

def _ver_tuple(s):
    try: return tuple(int(x) for x in str(s).lstrip("v").split("."))
    except: return (0,)

def _lerp_color(c1,c2,t):
    def h2r(h):
        h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
    r1,g1,b1=h2r(c1); r2,g2,b2=h2r(c2)
    return "#{:02x}{:02x}{:02x}".format(int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t))

def _load_json(path,default):
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f:
                d=json.load(f)
                return {**default,**d} if isinstance(default,dict) else d
        except: pass
    return default.copy() if isinstance(default,dict) else default

def _save_json(path,data):
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)

DEFAULT_SETTINGS={
    "username":"Player","ram":2048,"last_version":"","theme":"dark",
    "language":"en","jvm_args":"-XX:+UseG1GC -XX:MaxGCPauseMillis=50",
    "modrinth_server":"original","check_updates":True,
    "accent_color":"#5dbb63","gradient_theme":False,
    "gradient_colors":["#5dbb63","#3a8fd9"],
    "active_account":None,
}

# ══════════════════════════════════════════════════════════════════════════════
#  Reusable CTk widgets
# ══════════════════════════════════════════════════════════════════════════════
def CTkCard(parent, **kw):
    """Rounded frame used as a card."""
    p = _pal()
    return ctk.CTkFrame(parent, corner_radius=10,
                        fg_color=p["card"],
                        border_width=1, border_color=p["border"], **kw)

def CTkSep(parent):
    p=_pal()
    ctk.CTkFrame(parent,height=1,fg_color=p["border"],corner_radius=0).pack(fill="x",pady=8)

def CTkScrollFrame2(parent, **kw):
    """Alias with lighter colour."""
    p=_pal()
    return ctk.CTkScrollableFrame(parent, fg_color=p["bg"], **kw)

# ══════════════════════════════════════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════════════════════════════════════
class MiniLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings  = _load_json(SETTINGS_F, DEFAULT_SETTINGS)
        self.accounts  = _load_json(ACCOUNTS_F, []) if os.path.exists(ACCOUNTS_F) else []
        self.servers   = _load_json(SERVERS_F,  []) if os.path.exists(SERVERS_F)  else []
        self.instances = _load_json(INSTANCES_F,[]) if os.path.exists(INSTANCES_F) else []
        self._lang     = self.settings.get("language","en")

        # set ctk appearance BEFORE building UI
        theme = self.settings.get("theme","dark")
        ctk.set_appearance_mode("dark" if theme in ("dark","midnight","forest","ocean") else "light")

        self.mc_versions        = []
        self.installed_versions = []
        self.server_processes   = {}
        self._srv_join_counts   = {}
        self._update_info       = None
        self._java_path         = None
        self._skin_photo        = None
        self._grad_t            = 0.0
        self._accent            = self.settings.get("accent_color","#5dbb63")

        self.title(f"MiniLauncher  v{APP_VERSION}")
        self.geometry("1040x660")
        self.minsize(860,560)

        self._build_ui()
        self._load_versions_async()
        self._find_java_async()
        if self.settings.get("check_updates",True):
            threading.Thread(target=self._bg_update_check,daemon=True).start()
        if self.settings.get("gradient_theme",False):
            self.after(200,self._anim_gradient)

    # ── translate ─────────────────────────────────────────────────────────
    def _(self,key,**kw):
        lang=self._lang if self._lang in T else "en"
        s=T[lang].get(key,T["en"].get(key,key))
        return s.format(**kw) if kw else s

    # ══════════════════════════════════════════════════════════════════════
    #  MAIN LAYOUT
    # ══════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        p=_pal(); acc=self._accent

        self.grid_columnconfigure(1,weight=1)
        self.grid_rowconfigure(0,weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────
        self.sidebar=ctk.CTkFrame(self,width=180,corner_radius=0,
                                  fg_color=p["bg2"])
        self.sidebar.grid(row=0,column=0,sticky="nsew")
        self.sidebar.grid_rowconfigure(10,weight=1)
        self.sidebar.grid_propagate(False)

        # Logo
        logo_f=ctk.CTkFrame(self.sidebar,fg_color="transparent")
        logo_f.grid(row=0,column=0,sticky="ew",padx=14,pady=(16,4))
        logo_btn=ctk.CTkButton(logo_f,text="⛏ MiniLauncher",
                               font=ctk.CTkFont(size=14,weight="bold"),
                               fg_color="transparent",text_color=acc,
                               hover_color=p["bg3"],anchor="w",corner_radius=6,
                               command=lambda:webbrowser.open(GITHUB_URL))
        logo_btn.pack(fill="x")
        ctk.CTkLabel(logo_f,text=f"v{APP_VERSION}",
                     font=ctk.CTkFont(size=10),text_color=p["fg2"]).pack(anchor="w")
        self._logo_btn=logo_btn

        ctk.CTkFrame(self.sidebar,height=1,fg_color=p["border"],corner_radius=0
                     ).grid(row=1,column=0,sticky="ew",padx=10,pady=(4,6))

        # Account widget
        self.acc_frame=ctk.CTkFrame(self.sidebar,fg_color="transparent")
        self.acc_frame.grid(row=2,column=0,sticky="ew",padx=8,pady=(0,4))
        self._build_account_widget()

        ctk.CTkFrame(self.sidebar,height=1,fg_color=p["border"],corner_radius=0
                     ).grid(row=3,column=0,sticky="ew",padx=10,pady=(0,6))

        # Nav buttons
        self.nav_btns={}
        tabs=[("play","play"),("instances","instances"),("servers","servers"),
              ("modrinth","modrinth"),("lan","nav_lan"),("settings","settings")]
        for row_i,(key,lk) in enumerate(tabs,start=4):
            btn=ctk.CTkButton(self.sidebar,text=self._(lk),anchor="w",
                              font=ctk.CTkFont(size=13),corner_radius=8,
                              fg_color="transparent",text_color=p["fg2"],
                              hover_color=p["bg3"],
                              command=lambda k=key:self._show_tab(k))
            btn.grid(row=row_i,column=0,sticky="ew",padx=8,pady=2)
            self.nav_btns[key]=btn

        # Bottom: theme toggle
        ctk.CTkFrame(self.sidebar,height=1,fg_color=p["border"],corner_radius=0
                     ).grid(row=11,column=0,sticky="ew",padx=10,pady=(0,4))
        ctk.CTkButton(self.sidebar,text="🌙 / ☀  Theme",anchor="w",
                      font=ctk.CTkFont(size=11),corner_radius=8,
                      fg_color="transparent",text_color=p["fg2"],
                      hover_color=p["bg3"],
                      command=self._toggle_theme
                      ).grid(row=12,column=0,sticky="ew",padx=8,pady=(0,10))

        # Update banner (hidden by default)
        self.update_banner=ctk.CTkButton(self.sidebar,text="🔔  Update available!",
                                         fg_color="#e0a020",text_color="#1a1000",
                                         hover_color="#c08010",corner_radius=8,
                                         font=ctk.CTkFont(size=11,weight="bold"),
                                         command=self._open_update_page)

        # ── Content area ──────────────────────────────────────────────────
        self.content=ctk.CTkFrame(self,corner_radius=0,fg_color=p["bg"])
        self.content.grid(row=0,column=1,sticky="nsew")
        self.content.grid_columnconfigure(0,weight=1)
        self.content.grid_rowconfigure(0,weight=1)

        self.pages={}
        self.pages["play"]      = self._build_play_page()
        self.pages["instances"] = self._build_instances_page()
        self.pages["servers"]   = self._build_servers_page()
        self.pages["modrinth"]  = self._build_modrinth_page()
        self.pages["lan"]       = self._build_lan_page()
        self.pages["settings"]  = self._build_settings_page()

        self._show_tab("play")

    def _show_tab(self,key):
        p=_pal(); acc=self._accent
        for k,f in self.pages.items():
            f.grid_forget()
        self.pages[key].grid(row=0,column=0,sticky="nsew")
        for k,b in self.nav_btns.items():
            if k==key:
                b.configure(fg_color=p["bg3"],text_color=acc,
                            font=ctk.CTkFont(size=13,weight="bold"))
            else:
                b.configure(fg_color="transparent",text_color=p["fg2"],
                            font=ctk.CTkFont(size=13))
        if key=="servers":  self._srv_refresh_list()
        if key=="lan":      threading.Thread(target=self._lan_scan,daemon=True).start()
        if key=="modrinth": self._mr_auto_search()

    # ══════════════════════════════════════════════════════════════════════
    #  ACCOUNT WIDGET (sidebar)
    # ══════════════════════════════════════════════════════════════════════
    def _build_account_widget(self):
        for w in self.acc_frame.winfo_children(): w.destroy()
        p=_pal(); acc=self._get_active_account()
        row=ctk.CTkFrame(self.acc_frame,fg_color="transparent")
        row.pack(fill="x")

        self.skin_lbl=ctk.CTkLabel(row,text="",width=32,height=32)
        self.skin_lbl.pack(side="left",padx=(2,8))

        info=ctk.CTkFrame(row,fg_color="transparent")
        info.pack(side="left",fill="x",expand=True)
        name  = acc["username"] if acc else "No account"
        atype = acc.get("type","offline").upper() if acc else "OFFLINE"
        ctk.CTkLabel(info,text=name,font=ctk.CTkFont(size=11,weight="bold"),
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(info,text=atype,font=ctk.CTkFont(size=9),
                     text_color=self._accent,anchor="w").pack(anchor="w")

        ctk.CTkButton(row,text="👤",width=32,height=32,corner_radius=8,
                      fg_color="transparent",hover_color=p["bg3"],
                      font=ctk.CTkFont(size=14),
                      command=self._open_account_manager).pack(side="right",padx=4)

        if acc and PIL_OK:
            threading.Thread(target=self._load_skin,args=(acc,),daemon=True).start()

    def _get_active_account(self):
        aid=self.settings.get("active_account")
        if aid:
            a=next((a for a in self.accounts if a.get("id")==aid),None)
            if a: return a
        return self.accounts[0] if self.accounts else None

    def _load_skin(self,account):
        try:
            atype=account.get("type","offline"); username=account.get("username","")
            if atype=="ely":
                raw=http_get_bytes(ELY_SKIN_URL.format(username=username),timeout=6)
            elif atype=="microsoft":
                uid=account.get("uuid","").replace("-","")
                if not uid: return
                prof=http_get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uid}",timeout=6)
                import base64
                prop=next((p for p in prof.get("properties",[]) if p["name"]=="textures"),None)
                if not prop: return
                tex=json.loads(base64.b64decode(prop["value"]).decode())
                url=tex.get("textures",{}).get("SKIN",{}).get("url","")
                if not url: return
                raw=http_get_bytes(url,timeout=6)
            else:
                raw=http_get_bytes(f"https://minotar.net/helm/{username}/32.png",timeout=6)
            img=Image.open(BytesIO(raw)).convert("RGBA")
            if atype!="offline":
                face=img.crop((8,8,16,16)).resize((32,32),Image.NEAREST)
                if img.width>=64 and img.height>=64:
                    ov=img.crop((40,8,48,16)).resize((32,32),Image.NEAREST)
                    face=Image.alpha_composite(face,ov)
                mask=Image.new("L",(32,32),0)
                ImageDraw.Draw(mask).rounded_rectangle([0,0,31,31],radius=6,fill=255)
                face.putalpha(mask)
            else:
                face=img.resize((32,32),Image.NEAREST)
            self._skin_photo=ctk.CTkImage(face,size=(32,32))
            self.after(0,lambda:self.skin_lbl.configure(image=self._skin_photo,text=""))
        except: pass

    def _open_account_manager(self):
        p=_pal()
        win=ctk.CTkToplevel(self)
        win.title(self._("accounts_t")); win.geometry("540x460"); win.grab_set()

        ctk.CTkLabel(win,text=self._("accounts_t"),
                     font=ctk.CTkFont(size=16,weight="bold")).pack(pady=(16,8))

        lf=CTkScrollFrame2(win); lf.pack(fill="both",expand=True,padx=16,pady=(0,8))

        def refresh():
            for w in lf.winfo_children(): w.destroy()
            if not self.accounts:
                ctk.CTkLabel(lf,text=self._("no_accounts"),
                             text_color=p["fg2"]).pack(pady=20); return
            for acc in self.accounts:
                is_active=(acc.get("id")==self.settings.get("active_account"))
                card=CTkCard(lf); card.pack(fill="x",pady=4)
                left=ctk.CTkFrame(card,fg_color="transparent")
                left.pack(side="left",fill="both",expand=True,padx=12,pady=8)
                ctk.CTkLabel(left,text=acc.get("username","?"),
                             font=ctk.CTkFont(size=12,weight="bold" if is_active else "normal"),
                             text_color=self._accent if is_active else p["fg"]).pack(anchor="w")
                ctk.CTkLabel(left,text=acc.get("type","offline").upper(),
                             font=ctk.CTkFont(size=10),text_color=p["fg2"]).pack(anchor="w")
                right=ctk.CTkFrame(card,fg_color="transparent")
                right.pack(side="right",padx=8,pady=6)
                if not is_active:
                    self._btn(right,self._("active_lbl"),
                              lambda a=acc:(_set_active(a),refresh()),"acc").pack(pady=2)
                self._btn(right,self._("remove_acc"),
                          lambda a=acc:(_remove(a),refresh()),"ghost").pack(pady=2)

        def _set_active(acc):
            self.settings["active_account"]=acc.get("id")
            _save_json(SETTINGS_F,self.settings); self._build_account_widget()
        def _remove(acc):
            self.accounts=[a for a in self.accounts if a.get("id")!=acc.get("id")]
            _save_json(ACCOUNTS_F,self.accounts)
            if self.settings.get("active_account")==acc.get("id"):
                self.settings["active_account"]=self.accounts[0].get("id") if self.accounts else None
                _save_json(SETTINGS_F,self.settings)
            self._build_account_widget()

        refresh()
        br=ctk.CTkFrame(win,fg_color="transparent"); br.pack(pady=8)
        self._btn(br,self._("add_ms"),lambda:self._ms_login(win,refresh),"acc").pack(side="left",padx=4)
        self._btn(br,self._("add_ely"),lambda:self._ely_login(win,refresh),"ghost").pack(side="left",padx=4)
        self._btn(br,self._("add_offline"),lambda:self._offline_login(win,refresh),"ghost").pack(side="left",padx=4)

    # ── Microsoft ─────────────────────────────────────────────────────────
    def _ms_login(self,parent,refresh_cb):
        p=_pal()
        win=ctk.CTkToplevel(parent); win.title(self._("ms_auth_title"))
        win.geometry("480x260"); win.grab_set()
        msg_v=ctk.StringVar(value=self._("checking"))
        st_v =ctk.StringVar(value="")
        ctk.CTkLabel(win,textvariable=msg_v,font=ctk.CTkFont(size=11),
                     wraplength=440,justify="left").pack(expand=True,padx=24,pady=20)
        ctk.CTkLabel(win,textvariable=st_v,text_color=self._accent,
                     font=ctk.CTkFont(size=10)).pack()
        def do_auth():
            try:
                resp=http_post(MS_DEVICE_URL,{"client_id":MS_CLIENT_ID,"scope":MS_SCOPE})
                dev_code=resp["device_code"]; user_code=resp["user_code"]
                verify_url=resp.get("verification_uri","https://microsoft.com/devicelogin")
                interval=resp.get("interval",5); expires=resp.get("expires_in",300)
                msg=self._("ms_auth_msg",url=verify_url,code=user_code)
                self.after(0,lambda:msg_v.set(msg)); webbrowser.open(verify_url)
                deadline=time.time()+expires; td=None
                while time.time()<deadline:
                    time.sleep(interval)
                    try:
                        td=http_post(MS_TOKEN_URL,{"client_id":MS_CLIENT_ID,"device_code":dev_code,
                                     "grant_type":"urn:ietf:params:oauth:grant-type:device_code"})
                        if "access_token" in td: break
                        td=None
                    except Exception as e:
                        if "authorization_pending" in str(e): continue
                        break
                if not td or "access_token" not in td:
                    self.after(0,lambda:st_v.set("Auth failed or timed out.")); return
                ms_token=td["access_token"]
                xbl=http_post(XBL_URL,{"Properties":{"AuthMethod":"RPS","SiteName":"user.auth.xboxlive.com",
                              "RpsTicket":f"d={ms_token}"},"RelyingParty":"http://auth.xboxlive.com","TokenType":"JWT"})
                xbl_token=xbl["Token"]; uhs=xbl["DisplayClaims"]["xui"][0]["uhs"]
                xsts=http_post(XSTS_URL,{"Properties":{"SandboxId":"RETAIL","UserTokens":[xbl_token]},
                               "RelyingParty":"rp://api.minecraftservices.com/","TokenType":"JWT"})
                xsts_token=xsts["Token"]
                mc=http_post(MC_AUTH_URL,{"identityToken":f"XBL3.0 x={uhs};{xsts_token}"})
                mc_token=mc["access_token"]
                prof=http_get(MC_PROFILE,headers={"Authorization":f"Bearer {mc_token}"},timeout=8)
                username=prof.get("name","Unknown"); raw_id=prof.get("id","")
                uuid=(f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
                      if len(raw_id)==32 else raw_id)
                acc={"id":uuid,"username":username,"uuid":uuid,"type":"microsoft",
                     "access_token":mc_token,"refresh_token":td.get("refresh_token","")}
                self.accounts=[a for a in self.accounts if a.get("id")!=uuid]
                self.accounts.append(acc); _save_json(ACCOUNTS_F,self.accounts)
                if not self.settings.get("active_account"):
                    self.settings["active_account"]=uuid; _save_json(SETTINGS_F,self.settings)
                self.after(0,lambda:(refresh_cb(),self._build_account_widget(),win.destroy()))
            except Exception as ex: self.after(0,lambda:st_v.set(f"Error: {ex}"))
        threading.Thread(target=do_auth,daemon=True).start()

    # ── Ely.By ────────────────────────────────────────────────────────────
    def _ely_login(self,parent,refresh_cb):
        p=_pal()
        win=ctk.CTkToplevel(parent); win.title("Ely.By Login")
        win.geometry("360x240"); win.grab_set()
        form=ctk.CTkFrame(win,fg_color="transparent"); form.pack(fill="both",expand=True,padx=24,pady=16)
        ctk.CTkLabel(form,text=self._("ely_user"),anchor="w").pack(anchor="w")
        user_e=ctk.CTkEntry(form,placeholder_text="login@ely.by"); user_e.pack(fill="x",pady=(2,8))
        ctk.CTkLabel(form,text=self._("ely_pass"),anchor="w").pack(anchor="w")
        pass_e=ctk.CTkEntry(form,placeholder_text="••••••••",show="●"); pass_e.pack(fill="x",pady=(2,8))
        st_v=ctk.StringVar(value="")
        ctk.CTkLabel(form,textvariable=st_v,text_color=p["fg2"],font=ctk.CTkFont(size=10)).pack()
        def do_login():
            u=user_e.get().strip(); pw=pass_e.get().strip()
            if not u or not pw: return
            st_v.set("Logging in…")
            def bg():
                try:
                    resp=http_post(ELY_AUTH_URL,{"username":u,"password":pw,
                                   "clientToken":"MiniLauncher","requestUser":True})
                    at=resp["accessToken"]; prof=resp.get("selectedProfile",{})
                    name=prof.get("name",u); uid=prof.get("id","")
                    uuid=(f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
                          if len(uid)==32 else uid)
                    acc={"id":uuid or u,"username":name,"uuid":uuid,"type":"ely","access_token":at}
                    self.accounts=[a for a in self.accounts if a.get("id")!=(uuid or u)]
                    self.accounts.append(acc); _save_json(ACCOUNTS_F,self.accounts)
                    if not self.settings.get("active_account"):
                        self.settings["active_account"]=acc["id"]; _save_json(SETTINGS_F,self.settings)
                    self.after(0,lambda:(refresh_cb(),self._build_account_widget(),win.destroy()))
                except Exception as ex: self.after(0,lambda:st_v.set(f"Error: {ex}"))
            threading.Thread(target=bg,daemon=True).start()
        self._btn(form,self._("ely_login"),do_login,"acc").pack(pady=(4,0))

    # ── Offline ───────────────────────────────────────────────────────────
    def _offline_login(self,parent,refresh_cb):
        win=ctk.CTkToplevel(parent); win.title("Offline")
        win.geometry("320x160"); win.grab_set()
        form=ctk.CTkFrame(win,fg_color="transparent"); form.pack(fill="both",expand=True,padx=24,pady=20)
        ctk.CTkLabel(form,text=self._("offline_name"),anchor="w").pack(anchor="w")
        e=ctk.CTkEntry(form,placeholder_text="Player"); e.pack(fill="x",pady=6)
        e.insert(0,"Player")
        def add():
            name=e.get().strip() or "Player"
            uid=hashlib.md5(f"OfflinePlayer:{name}".encode()).hexdigest()
            uuid=f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
            acc={"id":uuid,"username":name,"uuid":uuid,"type":"offline","access_token":"0"}
            self.accounts=[a for a in self.accounts if a.get("id")!=uuid]
            self.accounts.append(acc); _save_json(ACCOUNTS_F,self.accounts)
            if not self.settings.get("active_account"):
                self.settings["active_account"]=uuid; _save_json(SETTINGS_F,self.settings)
            refresh_cb(); self._build_account_widget(); win.destroy()
        self._btn(form,"Add",add,"acc").pack(pady=4)

    # ══════════════════════════════════════════════════════════════════════
    #  PLAY PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _build_play_page(self):
        p=_pal()
        frame=ctk.CTkFrame(self.content,corner_radius=0,fg_color=p["bg"])
        frame.grid_columnconfigure(0,weight=1); frame.grid_rowconfigure(1,weight=1)

        # Header
        hdr=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=52)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(hdr,text=self._("play_title"),
                     font=ctk.CTkFont(size=16,weight="bold")).grid(row=0,column=0,sticky="w",padx=20,pady=12)
        self.java_status_lbl=ctk.CTkLabel(hdr,text="",font=ctk.CTkFont(size=10),text_color=p["fg2"])
        self.java_status_lbl.grid(row=0,column=1,sticky="e",padx=20)

        # Body
        body=CTkScrollFrame2(frame); body.grid(row=1,column=0,sticky="nsew")
        body.grid_columnconfigure(0,weight=1)

        # Instance row
        ir=ctk.CTkFrame(body,fg_color="transparent"); ir.pack(fill="x",padx=20,pady=(16,0))
        ctk.CTkLabel(ir,text="Instance:",font=ctk.CTkFont(size=12),width=120,anchor="w").pack(side="left")
        self.play_inst_var=ctk.StringVar(value="(default)")
        self.play_inst_combo=ctk.CTkComboBox(ir,variable=self.play_inst_var,
                                              values=["(default)"]+[i["name"] for i in self.instances],
                                              state="readonly",width=220)
        self.play_inst_combo.pack(side="left")

        # Version row
        vr=ctk.CTkFrame(body,fg_color="transparent"); vr.pack(fill="x",padx=20,pady=(12,0))
        ctk.CTkLabel(vr,text=self._("mc_ver"),font=ctk.CTkFont(size=12),width=120,anchor="w").pack(side="left")
        self.version_var=ctk.StringVar()
        self.version_combo=ctk.CTkComboBox(vr,variable=self.version_var,values=[],
                                            state="readonly",width=200)
        self.version_combo.pack(side="left",padx=(0,12))
        self.ver_type_var=ctk.StringVar(value="release")
        ctk.CTkRadioButton(vr,text=self._("releases"),variable=self.ver_type_var,value="release",
                           command=self._filter_versions).pack(side="left",padx=(0,8))
        ctk.CTkRadioButton(vr,text=self._("snapshots"),variable=self.ver_type_var,value="snapshot",
                           command=self._filter_versions).pack(side="left")

        # Buttons
        br=ctk.CTkFrame(body,fg_color="transparent"); br.pack(fill="x",padx=20,pady=12)
        self._btn(br,self._("btn_install"),self._install_version,"ghost").pack(side="left")
        self._btn(br,self._("btn_launch"),self._launch_game,"acc").pack(side="left",padx=(10,0))

        CTkSep(body)

        # Installed versions
        ctk.CTkLabel(body,text=self._("installed"),font=ctk.CTkFont(size=12),
                     text_color=p["fg2"]).pack(anchor="w",padx=20,pady=(0,4))
        self.installed_lb=ctk.CTkTextbox(body,height=80,font=ctk.CTkFont(family="Consolas",size=11),
                                          state="disabled",corner_radius=8)
        self.installed_lb.pack(fill="x",padx=20)

        CTkSep(body)

        # Log
        ctk.CTkLabel(body,text=self._("log_lbl"),font=ctk.CTkFont(size=12),
                     text_color=p["fg2"]).pack(anchor="w",padx=20,pady=(0,4))
        self.log_text=ctk.CTkTextbox(body,height=160,font=ctk.CTkFont(family="Consolas",size=10),
                                      state="disabled",corner_radius=8)
        self.log_text.pack(fill="both",expand=True,padx=20)

        # Progress
        self.progress_lbl=ctk.CTkLabel(body,text="",font=ctk.CTkFont(size=10),text_color=p["fg2"])
        self.progress_lbl.pack(anchor="w",padx=20,pady=(6,2))
        self.progress_bar=ctk.CTkProgressBar(body,height=6,progress_color=self._accent,corner_radius=3)
        self.progress_bar.pack(fill="x",padx=20,pady=(0,16))
        self.progress_bar.set(0)

        return frame

    # ══════════════════════════════════════════════════════════════════════
    #  INSTANCES PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _build_instances_page(self):
        p=_pal()
        frame=ctk.CTkFrame(self.content,corner_radius=0,fg_color=p["bg"])
        frame.grid_columnconfigure(0,weight=1); frame.grid_rowconfigure(1,weight=1)
        hdr=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=52)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
        ctk.CTkLabel(hdr,text=self._("inst_t"),font=ctk.CTkFont(size=16,weight="bold")
                     ).pack(side="left",padx=20,pady=12)
        self.inst_scroll=CTkScrollFrame2(frame)
        self.inst_scroll.grid(row=1,column=0,sticky="nsew")
        self.inst_scroll.grid_columnconfigure(0,weight=1)
        footer=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=54)
        footer.grid(row=2,column=0,sticky="ew"); footer.grid_propagate(False)
        self._btn(footer,self._("btn_new_inst"),self._inst_create_dialog,"acc").pack(pady=10)
        self._inst_refresh()
        return frame

    def _inst_refresh(self):
        for w in self.inst_scroll.winfo_children(): w.destroy()
        if not self.instances:
            ctk.CTkLabel(self.inst_scroll,text=self._("no_inst"),
                         text_color=_pal()["fg2"],font=ctk.CTkFont(size=13)).pack(pady=40); return
        for inst in self.instances: self._inst_add_card(inst)

    def _inst_add_card(self,inst):
        p=_pal()
        name=inst.get("name","?"); ver=inst.get("mc_version","?")
        loader=inst.get("loader","Vanilla"); l_ver=inst.get("loader_version","")
        lcolor=SERVER_CORES.get(loader,{}).get("color",self._accent)

        card=ctk.CTkFrame(self.inst_scroll,corner_radius=10,
                          fg_color=p["card"],border_width=1,border_color=p["border"])
        card.pack(fill="x",padx=16,pady=5)

        # colour stripe
        stripe=ctk.CTkFrame(card,width=6,corner_radius=0,fg_color=lcolor)
        stripe.pack(side="left",fill="y")

        body=ctk.CTkFrame(card,fg_color="transparent")
        body.pack(side="left",fill="both",expand=True,padx=14,pady=10)
        ctk.CTkLabel(body,text=name,font=ctk.CTkFont(size=13,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(body,text=f"MC {ver}  •  {loader} {l_ver}",
                     font=ctk.CTkFont(size=11),text_color=p["fg2"]).pack(anchor="w",pady=(2,0))
        mods_dir=inst.get("mods_dir","")
        if mods_dir and os.path.exists(mods_dir):
            n=len([f for f in os.listdir(mods_dir) if f.endswith(".jar")])
            ctk.CTkLabel(body,text=f"{n} mods",font=ctk.CTkFont(size=10),text_color=p["fg2"]).pack(anchor="w")

        btns=ctk.CTkFrame(card,fg_color="transparent")
        btns.pack(side="right",padx=10,pady=8)
        self._btn(btns,"▶ Launch",lambda n=name:self._launch_instance(n),"acc").pack(fill="x",pady=2)
        self._btn(btns,"📂 Folder",lambda d=inst.get("dir",""):self._open_folder(d),"ghost").pack(fill="x",pady=2)
        self._btn(btns,self._("delete"),lambda n=name:self._inst_delete(n),"ghost").pack(fill="x",pady=2)

    def _open_folder(self,path):
        if not path or not os.path.exists(path): return
        if sys.platform=="win32": os.startfile(path)
        elif sys.platform=="darwin": subprocess.Popen(["open",path])
        else: subprocess.Popen(["xdg-open",path])

    def _inst_create_dialog(self):
        p=_pal()
        win=ctk.CTkToplevel(self); win.title(self._("new_inst"))
        win.geometry("440x380"); win.grab_set()
        ctk.CTkLabel(win,text=self._("new_inst"),font=ctk.CTkFont(size=16,weight="bold")).pack(pady=(16,8))
        form=ctk.CTkFrame(win,fg_color="transparent"); form.pack(fill="x",padx=24)
        def frow(lk,opts=None,default=""):
            r=ctk.CTkFrame(form,fg_color="transparent"); r.pack(fill="x",pady=4)
            ctk.CTkLabel(r,text=self._(lk),width=130,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
            v=ctk.StringVar(value=default)
            if opts: w=ctk.CTkComboBox(r,variable=v,values=opts,state="readonly",width=200)
            else:    w=ctk.CTkEntry(r,textvariable=v,width=200,placeholder_text=default)
            w.pack(side="left"); return v
        name_v  = frow("inst_name",default="My Instance")
        mc_list = [v["id"] for v in self.mc_versions if v["type"]=="release"][:40] or ["1.21.4"]
        ver_v   = frow("inst_ver",mc_list,mc_list[0] if mc_list else "1.21.4")
        load_v  = frow("inst_loader",["Vanilla","Fabric","Forge","NeoForge","Quilt"],"Vanilla")
        lver_v  = frow("inst_lver",default="latest")
        st_v=ctk.StringVar(value="")
        ctk.CTkLabel(form,textvariable=st_v,font=ctk.CTkFont(size=11),
                     text_color=self._accent).pack(anchor="w",pady=4)
        br=ctk.CTkFrame(win,fg_color="transparent"); br.pack(pady=8)
        def do_create():
            n=name_v.get().strip()
            if not n: return
            if any(i["name"]==n for i in self.instances):
                messagebox.showwarning(self._("warn"),f"«{n}» exists"); return
            mc_ver=ver_v.get(); loader=load_v.get(); l_ver=lver_v.get().strip() or "latest"
            inst_dir=os.path.join(INSTANCES_DIR,n); mods_dir=os.path.join(inst_dir,"mods")
            os.makedirs(mods_dir,exist_ok=True)
            inst={"name":n,"mc_version":mc_ver,"loader":loader,
                  "loader_version":l_ver,"dir":inst_dir,"mods_dir":mods_dir}
            self.instances.append(inst); _save_json(INSTANCES_F,self.instances)
            st_v.set(f"Installing {loader} {mc_ver}…")
            def bg():
                try:
                    cbs={"setStatus":lambda s:self.after(0,lambda:st_v.set(s)),
                         "setProgress":lambda v:None,"setMax":lambda v:None}
                    if loader=="Fabric":
                        inst_l=http_get("https://meta.fabricmc.net/v2/versions/installer",timeout=10)[0]["version"]
                        ldr_l =http_get("https://meta.fabricmc.net/v2/versions/loader",timeout=10)[0]["version"]
                        url=(f"https://meta.fabricmc.net/v2/versions/loader/{mc_ver}/{ldr_l}/{inst_l}/server/jar")
                        dest=os.path.join(inst_dir,f"fabric-server-{mc_ver}.jar")
                        http_download(url,dest,lambda d,t:st_v.set(f"Fabric {int(d/t*100)}%"))
                    elif loader=="Quilt":
                        ldr_l=http_get("https://meta.quiltmc.org/v3/versions/loader",timeout=10)[0]["version"]
                        url=(f"https://meta.quiltmc.org/v3/versions/loader/{mc_ver}/{ldr_l}/server/jar")
                        dest=os.path.join(inst_dir,f"quilt-server-{mc_ver}.jar")
                        http_download(url,dest,lambda d,t:st_v.set(f"Quilt {int(d/t*100)}%"))
                    else:
                        minecraft_launcher_lib.install.install_minecraft_version(mc_ver,inst_dir,callback=cbs)
                    self.after(0,lambda:(self._inst_refresh(),self._refresh_play_instances(),win.destroy()))
                except Exception as ex: self.after(0,lambda:st_v.set(f"✗ {ex}"))
            threading.Thread(target=bg,daemon=True).start()
        self._btn(br,"Create",do_create,"acc").pack(side="left",padx=4)
        self._btn(br,self._("cancel"),win.destroy,"ghost").pack(side="left",padx=4)

    def _inst_delete(self,name):
        if not messagebox.askyesno(self._("warn"),f"Delete instance «{name}»?"): return
        inst=next((i for i in self.instances if i["name"]==name),None)
        if inst and os.path.exists(inst.get("dir","")): shutil.rmtree(inst["dir"],ignore_errors=True)
        self.instances=[i for i in self.instances if i["name"]!=name]
        _save_json(INSTANCES_F,self.instances); self._inst_refresh(); self._refresh_play_instances()

    def _launch_instance(self,name):
        inst=next((i for i in self.instances if i["name"]==name),None)
        if not inst: return
        self.play_inst_var.set(name); self.version_var.set(inst["mc_version"])
        self._show_tab("play"); self._launch_game()

    def _refresh_play_instances(self):
        try:
            names=["(default)"]+[i["name"] for i in self.instances]
            self.play_inst_combo.configure(values=names)
            self.mr_inst_combo.configure(values=names)
        except: pass

    # ══════════════════════════════════════════════════════════════════════
    #  SERVERS PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _build_servers_page(self):
        p=_pal()
        frame=ctk.CTkFrame(self.content,corner_radius=0,fg_color=p["bg"])
        frame.grid_columnconfigure(0,weight=1); frame.grid_rowconfigure(1,weight=1)
        hdr=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=52)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
        ctk.CTkLabel(hdr,text=self._("servers_title"),font=ctk.CTkFont(size=16,weight="bold")
                     ).pack(side="left",padx=20,pady=12)
        self.srv_scroll=CTkScrollFrame2(frame)
        self.srv_scroll.grid(row=1,column=0,sticky="nsew")
        self.srv_scroll.grid_columnconfigure(0,weight=1)
        footer=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=54)
        footer.grid(row=2,column=0,sticky="ew"); footer.grid_propagate(False)
        self._btn(footer,self._("btn_create_srv"),self._srv_create_dialog,"acc").pack(pady=10)
        return frame

    def _srv_refresh_list(self):
        for w in self.srv_scroll.winfo_children(): w.destroy()
        if not self.servers:
            ctk.CTkLabel(self.srv_scroll,text=self._("no_servers"),
                         text_color=_pal()["fg2"],font=ctk.CTkFont(size=13)).pack(pady=40); return
        for srv in self.servers: self._srv_add_card(srv)

    def _srv_add_card(self,srv):
        p=_pal()
        name=srv.get("name","Server"); core=srv.get("core","Paper")
        ver=srv.get("version","?"); port=srv.get("port",25565)
        proc=self.server_processes.get(name); online=proc and proc.poll() is None
        sc="#5dbb63" if online else "#e05050"
        cc=SERVER_CORES.get(core,{}).get("color","#888")

        card=ctk.CTkFrame(self.srv_scroll,corner_radius=10,
                          fg_color=p["card"],border_width=1,border_color=p["border"])
        card.pack(fill="x",padx=16,pady=5)
        stripe=ctk.CTkFrame(card,width=6,corner_radius=0,fg_color=sc)
        stripe.pack(side="left",fill="y")

        info=ctk.CTkFrame(card,fg_color="transparent")
        info.pack(side="left",fill="both",expand=True,padx=14,pady=10)
        r1=ctk.CTkFrame(info,fg_color="transparent"); r1.pack(anchor="w",fill="x")
        ctk.CTkLabel(r1,text=name,font=ctk.CTkFont(size=13,weight="bold")).pack(side="left")
        ctk.CTkLabel(r1,text=f"  {'● online' if online else '○ offline'}",
                     text_color=sc,font=ctk.CTkFont(size=11)).pack(side="left")
        r2=ctk.CTkFrame(info,fg_color="transparent"); r2.pack(anchor="w",pady=(3,0))
        ctk.CTkLabel(r2,text=core,text_color=cc,font=ctk.CTkFont(size=11,weight="bold")).pack(side="left")
        ctk.CTkLabel(r2,text=f"  {ver}  •  :{port}",
                     text_color=p["fg2"],font=ctk.CTkFont(size=11)).pack(side="left")

        btns=ctk.CTkFrame(card,fg_color="transparent")
        btns.pack(side="right",padx=10,pady=8)
        if online:
            self._btn(btns,self._("stop"),    lambda n=name:self._srv_stop(n),"ghost").pack(fill="x",pady=2)
        else:
            self._btn(btns,self._("start"),   lambda n=name:self._srv_start(n),"acc").pack(fill="x",pady=2)
        self._btn(btns,self._("console"),     lambda n=name:self._srv_open_console(n),"ghost").pack(fill="x",pady=2)
        self._btn(btns,self._("dashboard"),   lambda n=name:self._srv_dashboard(n),"ghost").pack(fill="x",pady=2)
        self._btn(btns,self._("plugins"),     lambda n=name:self._srv_open_plugins(n),"ghost").pack(fill="x",pady=2)
        self._btn(btns,self._("delete"),      lambda n=name:self._srv_delete(n),"ghost").pack(fill="x",pady=2)

    # ── Server create dialog ──────────────────────────────────────────────
    def _srv_create_dialog(self):
        p=_pal()
        win=ctk.CTkToplevel(self); win.title(self._("new_srv"))
        win.geometry("500x500"); win.grab_set()
        ctk.CTkLabel(win,text=self._("new_srv"),font=ctk.CTkFont(size=16,weight="bold")).pack(pady=(16,8))
        form=ctk.CTkFrame(win,fg_color="transparent"); form.pack(fill="x",padx=24)

        ctk.CTkLabel(form,text=self._("srv_name"),anchor="w",font=ctk.CTkFont(size=12)).pack(anchor="w")
        name_e=ctk.CTkEntry(form,placeholder_text="My Server"); name_e.pack(fill="x",pady=(2,8))

        ctk.CTkLabel(form,text=self._("srv_core"),anchor="w",font=ctk.CTkFont(size=12)).pack(anchor="w")
        core_v=ctk.StringVar(value="Paper")
        core_cb=ctk.CTkComboBox(form,variable=core_v,values=list(SERVER_CORES.keys()),
                                 state="readonly",width=280); core_cb.pack(anchor="w",pady=(2,8))

        ctk.CTkLabel(form,text=self._("srv_ver"),anchor="w",font=ctk.CTkFont(size=12)).pack(anchor="w")
        ver_v=ctk.StringVar(value="1.21.4")
        ver_cb=ctk.CTkComboBox(form,variable=ver_v,values=SERVER_CORES["Paper"]["versions"],
                                state="readonly",width=280); ver_cb.pack(anchor="w",pady=(2,8))
        def on_core(_=None):
            c=core_v.get(); vers=SERVER_CORES.get(c,{}).get("versions",["latest"])
            ver_cb.configure(values=vers); ver_v.set(vers[0])
            desc_lbl.configure(text=SERVER_CORES.get(c,{}).get("desc",""),
                               text_color=SERVER_CORES.get(c,{}).get("color",self._accent))
        core_v.trace_add("write",lambda *_:on_core())

        r=ctk.CTkFrame(form,fg_color="transparent"); r.pack(fill="x",pady=(0,8))
        ctk.CTkLabel(r,text=self._("srv_port"),width=80,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        port_e=ctk.CTkEntry(r,width=100,placeholder_text="25565"); port_e.pack(side="left",padx=(0,20))
        port_e.insert(0,"25565")
        ctk.CTkLabel(r,text=self._("srv_ram"),width=80,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        ram_e=ctk.CTkEntry(r,width=100,placeholder_text="1024"); ram_e.pack(side="left")
        ram_e.insert(0,"1024")

        desc_lbl=ctk.CTkLabel(form,text=SERVER_CORES["Paper"]["desc"],
                               text_color=SERVER_CORES["Paper"]["color"],
                               font=ctk.CTkFont(size=11),wraplength=440,justify="left")
        desc_lbl.pack(anchor="w",pady=(0,4))

        st_v=ctk.StringVar(value="")
        ctk.CTkLabel(form,textvariable=st_v,text_color=self._accent,font=ctk.CTkFont(size=11)).pack(anchor="w")
        br=ctk.CTkFrame(win,fg_color="transparent"); br.pack(pady=8)

        def do_create():
            n=name_e.get().strip()
            if not n: messagebox.showwarning(self._("warn"),self._("name_empty")); return
            if any(s["name"]==n for s in self.servers):
                messagebox.showwarning(self._("warn"),self._("name_exists",n=n)); return
            try: port=int(port_e.get()); ram=int(ram_e.get())
            except: messagebox.showwarning(self._("warn"),self._("port_invalid")); return
            core=core_v.get(); ver=ver_v.get()
            srv_dir=os.path.join(SERVERS_DIR,n); os.makedirs(srv_dir,exist_ok=True)
            new_srv={"name":n,"core":core,"version":ver,"port":port,"ram":ram,"dir":srv_dir,"jar":""}
            self.servers.append(new_srv); _save_json(SERVERS_F,self.servers)
            st_v.set(self._("creating",core=core,ver=ver))
            threading.Thread(target=self._srv_download_core,args=(new_srv,st_v,win),daemon=True).start()

        self._btn(br,self._("btn_create"),do_create,"acc").pack(side="left",padx=4)
        self._btn(br,self._("cancel"),win.destroy,"ghost").pack(side="left",padx=4)

    def _srv_download_core(self,srv,st_v,win):
        core=srv["core"]; ver=srv["version"]; d=srv["dir"]
        def upd(m): self.after(0,lambda:st_v.set(m))
        try:
            jar=""
            if core=="Paper":       jar=self._dl_paper(ver,d,upd)
            elif core=="Purpur":    jar=self._dl_purpur(ver,d,upd)
            elif core=="Velocity":  jar=self._dl_velocity(d,upd)
            elif core=="Waterfall": jar=self._dl_waterfall(d,upd)
            elif core=="BungeeCord":jar=self._dl_bungeecord(d,upd)
            elif core=="Fabric":    jar=self._dl_fabric(ver,d,upd)
            elif core=="Vanilla":   jar=self._dl_vanilla(ver,d,upd)
            else:
                jar=os.path.join(d,f"{core.lower()}-server.jar")
                upd(f"⚠ Place {core} jar manually at:\n{jar}")
            for s in self.servers:
                if s["name"]==srv["name"]: s["jar"]=jar; break
            _save_json(SERVERS_F,self.servers)
            for fname,content in [("eula.txt","eula=true\n"),
                ("server.properties",f"server-port={srv['port']}\nonline-mode=false\nmotd=MiniLauncher\n")]:
                fp=os.path.join(d,fname)
                if not os.path.exists(fp):
                    with open(fp,"w") as f: f.write(content)
            upd(self._("srv_ready",core=core,ver=ver))
            self.after(0,self._srv_refresh_list)
            self.after(2500,lambda:self._safe_close(win))
        except Exception as ex: upd(f"✗ {ex}")

    def _safe_close(self,win):
        try: win.destroy()
        except: pass

    def _dl_paper(self,ver,d,upd):
        upd(f"Fetching Paper {ver}…")
        b=http_get(f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds",timeout=10)
        l=b["builds"][-1]["build"]; jar=f"paper-{ver}-{l}.jar"
        dest=os.path.join(d,jar)
        http_download(f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds/{l}/downloads/{jar}",
                      dest,lambda dn,t:upd(f"Paper {ver}  {int(dn/t*100)}%  ({dn//1024} KB)")); return dest
    def _dl_purpur(self,ver,d,upd):
        upd(f"Fetching Purpur {ver}…")
        data=http_get(f"https://api.purpurmc.org/v2/purpur/{ver}",timeout=10)
        bid=data["builds"]["latest"]; dest=os.path.join(d,f"purpur-{ver}-{bid}.jar")
        http_download(f"https://api.purpurmc.org/v2/purpur/{ver}/{bid}/download",
                      dest,lambda dn,t:upd(f"Purpur {ver}  {int(dn/t*100)}%")); return dest
    def _dl_velocity(self,d,upd):
        upd("Fetching Velocity…")
        b=http_get("https://api.papermc.io/v2/projects/velocity/versions/3.3.0-SNAPSHOT/builds",timeout=10)
        l=b["builds"][-1]["build"]; jar=f"velocity-3.3.0-SNAPSHOT-{l}.jar"
        dest=os.path.join(d,jar)
        http_download(f"https://api.papermc.io/v2/projects/velocity/versions/3.3.0-SNAPSHOT/builds/{l}/downloads/{jar}",
                      dest,lambda dn,t:upd(f"Velocity  {int(dn/t*100)}%")); return dest
    def _dl_waterfall(self,d,upd):
        upd("Fetching Waterfall…")
        b=http_get("https://api.papermc.io/v2/projects/waterfall/versions/1.21/builds",timeout=10)
        l=b["builds"][-1]["build"]; jar=f"waterfall-1.21-{l}.jar"
        dest=os.path.join(d,jar)
        http_download(f"https://api.papermc.io/v2/projects/waterfall/versions/1.21/builds/{l}/downloads/{jar}",
                      dest,lambda dn,t:upd(f"Waterfall  {int(dn/t*100)}%")); return dest
    def _dl_bungeecord(self,d,upd):
        upd("Downloading BungeeCord…"); dest=os.path.join(d,"BungeeCord.jar")
        http_download("https://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar",
                      dest,lambda dn,t:upd(f"BungeeCord  {int(dn/t*100) if t else 0}%")); return dest
    def _dl_fabric(self,ver,d,upd):
        upd(f"Fetching Fabric {ver}…")
        inst=http_get("https://meta.fabricmc.net/v2/versions/installer",timeout=10)[0]["version"]
        load=http_get("https://meta.fabricmc.net/v2/versions/loader",timeout=10)[0]["version"]
        dest=os.path.join(d,f"fabric-server-{ver}.jar")
        http_download(f"https://meta.fabricmc.net/v2/versions/loader/{ver}/{load}/{inst}/server/jar",
                      dest,lambda dn,t:upd(f"Fabric {int(dn/t*100)}%")); return dest
    def _dl_vanilla(self,ver,d,upd):
        upd("Fetching manifest…")
        mf=http_get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",timeout=10)
        vi=next((v for v in mf["versions"] if v["id"]==ver),None)
        if not vi: raise ValueError(f"Version {ver} not found")
        url=http_get(vi["url"],timeout=10)["downloads"]["server"]["url"]
        dest=os.path.join(d,f"minecraft_server.{ver}.jar")
        http_download(url,dest,lambda dn,t:upd(f"Vanilla {ver}  {int(dn/t*100)}%")); return dest

    def _srv_start(self,name):
        srv=next((s for s in self.servers if s["name"]==name),None)
        if not srv: return
        jar=srv.get("jar","")
        if not jar or not os.path.exists(jar):
            messagebox.showerror(self._("err"),self._("no_jar")); return
        java=self._find_java() or "java"; ram=srv.get("ram",1024)
        cmd=[java,f"-Xmx{ram}M",f"-Xms{min(ram,512)}M","-jar",jar,"nogui"]
        try:
            proc=subprocess.Popen(cmd,cwd=srv["dir"],stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            self.server_processes[name]=proc; self._srv_refresh_list()
            threading.Thread(target=self._srv_read_log,args=(name,proc),daemon=True).start()
        except FileNotFoundError: messagebox.showerror(self._("err"),self._("java_err"))

    def _srv_stop(self,name):
        proc=self.server_processes.get(name)
        if proc and proc.poll() is None:
            try: proc.stdin.write("stop\n"); proc.stdin.flush()
            except: proc.terminate()
        self.after(2000,self._srv_refresh_list)

    def _srv_read_log(self,name,proc):
        for line in proc.stdout:
            if " joined the game" in line:
                self._srv_join_counts[name]=self._srv_join_counts.get(name,0)+1
        proc.wait(); self.after(500,self._srv_refresh_list)

    def _srv_delete(self,name):
        if not messagebox.askyesno(self._("warn"),self._("delete_q",n=name)): return
        proc=self.server_processes.get(name)
        if proc and proc.poll() is None: proc.terminate()
        srv=next((s for s in self.servers if s["name"]==name),None)
        if srv and os.path.exists(srv.get("dir","")): shutil.rmtree(srv["dir"],ignore_errors=True)
        self.servers=[s for s in self.servers if s["name"]!=name]
        _save_json(SERVERS_F,self.servers); self._srv_refresh_list()

    def _srv_open_console(self,name):
        p=_pal(); proc=self.server_processes.get(name)
        win=ctk.CTkToplevel(self); win.title(f"Console — {name}"); win.geometry("720x480")
        ctk.CTkLabel(win,text=f"Console: {name}",font=ctk.CTkFont(size=13,weight="bold")).pack(pady=(12,4))
        log=ctk.CTkTextbox(win,font=ctk.CTkFont(family="Consolas",size=10),
                            state="disabled",corner_radius=8)
        log.pack(fill="both",expand=True,padx=12,pady=(0,6))
        row=ctk.CTkFrame(win,fg_color="transparent"); row.pack(fill="x",padx=12,pady=(0,12))
        cv=ctk.StringVar()
        ce=ctk.CTkEntry(row,textvariable=cv,placeholder_text="command…",corner_radius=8)
        ce.pack(side="left",fill="x",expand=True,padx=(0,8))
        def send(*_):
            if proc and proc.poll() is None:
                try: proc.stdin.write(cv.get()+"\n"); proc.stdin.flush(); cv.set("")
                except: pass
        ce.bind("<Return>",send)
        self._btn(row,self._("send"),send,"acc").pack(side="left")
        msg=self._("srv_on",n=name) if (proc and proc.poll() is None) else self._("srv_off",n=name)
        self._tbox_append(log,msg+"\n")
        if proc and proc.poll() is None:
            def _read():
                for line in proc.stdout: self.after(0,lambda l=line:self._tbox_append(log,l))
            threading.Thread(target=_read,daemon=True).start()

    def _tbox_append(self,w,text):
        try: w.configure(state="normal"); w.insert("end",text); w.see("end"); w.configure(state="disabled")
        except: pass

    # ── Server Dashboard ──────────────────────────────────────────────────
    def _srv_dashboard(self,name):
        p=_pal(); proc=self.server_processes.get(name)
        win=ctk.CTkToplevel(self); win.title(self._("dash_t",n=name)); win.geometry("700x520")
        ctk.CTkLabel(win,text=self._("dash_t",n=name),
                     font=ctk.CTkFont(size=14,weight="bold")).pack(pady=(14,8))
        main=ctk.CTkFrame(win,fg_color="transparent"); main.pack(fill="both",expand=True,padx=16)
        main.columnconfigure(0,weight=1); main.columnconfigure(1,weight=0)
        left=ctk.CTkFrame(main,fg_color="transparent"); left.grid(row=0,column=0,sticky="nsew")
        right=ctk.CTkFrame(main,width=200,fg_color="transparent"); right.grid(row=0,column=1,sticky="nsew",padx=(14,0))

        ctk.CTkLabel(left,text=self._("dash_players"),font=ctk.CTkFont(size=12,weight="bold")).pack(anchor="w")
        players_v=ctk.StringVar(value="—")
        ctk.CTkLabel(left,textvariable=players_v,font=ctk.CTkFont(size=11),
                     corner_radius=8,fg_color=p["bg3"],anchor="w").pack(fill="x",pady=(4,10),ipady=8)

        act=ctk.CTkFrame(left,fg_color="transparent"); act.pack(fill="x",pady=(0,10))
        pe=ctk.CTkEntry(act,placeholder_text="player name",width=160); pe.pack(side="left",padx=(0,8))
        def mc_cmd(c):
            pl=pe.get().strip()
            if pl and proc and proc.poll() is None:
                try: proc.stdin.write(f"{c} {pl}\n"); proc.stdin.flush()
                except: pass
        self._btn(act,self._("dash_op"),  lambda:mc_cmd("op"),  "ghost").pack(side="left",padx=2)
        self._btn(act,self._("dash_kick"),lambda:mc_cmd("kick"),"ghost").pack(side="left",padx=2)
        self._btn(act,self._("dash_ban"), lambda:mc_cmd("ban"), "ghost").pack(side="left",padx=2)

        ctk.CTkLabel(left,text=self._("dash_cpu"),font=ctk.CTkFont(size=12,weight="bold")).pack(anchor="w")
        ram_v=ctk.StringVar(value="—")
        ctk.CTkLabel(left,textvariable=ram_v,font=ctk.CTkFont(family="Consolas",size=11),
                     text_color=self._accent).pack(anchor="w",pady=(4,0))

        ctk.CTkLabel(right,text=self._("dash_total"),font=ctk.CTkFont(size=11),text_color=p["fg2"]).pack(anchor="w")
        total_v=ctk.StringVar(value=str(self._srv_join_counts.get(name,0)))
        ctk.CTkLabel(right,textvariable=total_v,font=ctk.CTkFont(size=28,weight="bold"),
                     text_color=self._accent).pack(anchor="w",pady=(0,12))
        ctk.CTkLabel(right,text="Server log",font=ctk.CTkFont(size=11),text_color=p["fg2"]).pack(anchor="w")
        mini=ctk.CTkTextbox(right,font=ctk.CTkFont(family="Consolas",size=8),
                             state="disabled",height=240,corner_radius=8)
        mini.pack(fill="both",expand=True)

        def refresh():
            if not win.winfo_exists(): return
            if proc and proc.poll() is None:
                try: proc.stdin.write("list\n"); proc.stdin.flush()
                except: pass
                try:
                    if sys.platform=="linux":
                        with open(f"/proc/{proc.pid}/status") as pf:
                            for line in pf:
                                if "VmRSS" in line:
                                    ram_v.set(f"RAM: {int(line.split()[1])//1024} MB"); break
                    elif sys.platform=="win32":
                        r=subprocess.check_output(f"wmic process where ProcessId={proc.pid} get WorkingSetSize",
                                                  shell=True,text=True)
                        nums=[x for x in r.split() if x.isdigit()]
                        if nums: ram_v.set(f"RAM: {int(nums[0])//1048576} MB")
                except: pass
            win.after(3000,refresh)
        win.after(500,refresh)
        if proc and proc.poll() is None:
            def _read():
                for line in proc.stdout:
                    if not win.winfo_exists(): break
                    self.after(0,lambda l=line:self._tbox_append(mini,l))
                    if " joined the game" in line:
                        self._srv_join_counts[name]=self._srv_join_counts.get(name,0)+1
                        self.after(0,lambda:total_v.set(str(self._srv_join_counts.get(name,0))))
                    if "players online" in line.lower():
                        self.after(0,lambda l=line:players_v.set(l.strip()))
            threading.Thread(target=_read,daemon=True).start()

    # ── Plugins ───────────────────────────────────────────────────────────
    def _srv_open_plugins(self,name):
        p=_pal(); srv=next((s for s in self.servers if s["name"]==name),None)
        if not srv: return
        win=ctk.CTkToplevel(self); win.title(self._("plugins_t",n=name)); win.geometry("720x540")
        ctk.CTkLabel(win,text=self._("plugins_t",n=name),
                     font=ctk.CTkFont(size=14,weight="bold")).pack(pady=(14,8))
        sf=ctk.CTkFrame(win,fg_color="transparent"); sf.pack(fill="x",padx=14,pady=(0,6))
        qv=ctk.StringVar(); st_v=ctk.StringVar(value="Search plugins on Modrinth")
        qe=ctk.CTkEntry(sf,textvariable=qv,placeholder_text="plugin name…",corner_radius=8)
        qe.pack(side="left",fill="x",expand=True,padx=(0,8))
        ctk.CTkLabel(sf,textvariable=st_v,text_color=p["fg2"],font=ctk.CTkFont(size=10)).pack(side="right")
        scroll=CTkScrollFrame2(win); scroll.pack(fill="both",expand=True,padx=14)
        scroll.grid_columnconfigure(0,weight=1)
        plugins_dir=os.path.join(srv["dir"],"plugins"); os.makedirs(plugins_dir,exist_ok=True)
        def add_card(item):
            pid=item.get("project_id",item.get("slug","")); pname=item.get("title","?")
            desc=item.get("description","")[:120]; dl=item.get("downloads",0)
            dl_fmt=f"{dl:,}".replace(",","_").replace("_"," ")
            card=ctk.CTkFrame(scroll,corner_radius=8,fg_color=p["card"],
                              border_width=1,border_color=p["border"])
            card.pack(fill="x",pady=4)
            ctk.CTkFrame(card,width=6,corner_radius=0,fg_color="#e05060").pack(side="left",fill="y")
            body=ctk.CTkFrame(card,fg_color="transparent")
            body.pack(side="left",fill="both",expand=True,padx=12,pady=8)
            ctk.CTkLabel(body,text=pname,font=ctk.CTkFont(size=12,weight="bold")).pack(anchor="w")
            ctk.CTkLabel(body,text=desc,font=ctk.CTkFont(size=10),text_color=p["fg2"],
                         wraplength=440).pack(anchor="w")
            ctk.CTkLabel(body,text=f"⬇ {dl_fmt}",font=ctk.CTkFont(size=10),
                         text_color=p["fg2"]).pack(anchor="w",pady=(2,0))
            rb=ctk.CTkFrame(card,fg_color="transparent"); rb.pack(side="right",padx=8,pady=8)
            self._btn(rb,"⬇ Get",lambda pid=pid:threading.Thread(
                target=self._plugin_dl,args=(pid,plugins_dir,st_v,win),daemon=True).start(),"acc").pack()
        def search(q=""):
            for w in scroll.winfo_children(): w.destroy()
            st_v.set("Searching…")
            def bg():
                api=MODRINTH_API[self.settings.get("modrinth_server","original")]
                try:
                    data=http_get(f"{api}/search",params={"query":q,"limit":20,
                        "facets":json.dumps([["project_type:plugin"]])},timeout=10)
                    hits=data.get("hits",[])
                    self.after(0,lambda:st_v.set(f"Found: {len(hits)}"))
                    for item in hits: self.after(0,lambda m=item:add_card(m))
                except Exception as ex: self.after(0,lambda:st_v.set(f"Error: {ex}"))
            threading.Thread(target=bg,daemon=True).start()
        qe.bind("<Return>",lambda e:search(qv.get().strip()))
        self._btn(sf,"Search",lambda:search(qv.get().strip()),"acc").pack(side="left")
        search("")

    def _plugin_dl(self,pid,plugins_dir,st_v,win):
        api=MODRINTH_API[self.settings.get("modrinth_server","original")]
        try:
            self.after(0,lambda:st_v.set("Fetching…"))
            vers=http_get(f"{api}/project/{pid}/version",timeout=10)
            if not vers: self.after(0,lambda:st_v.set("No files")); return
            files=vers[0].get("files",[])
            target=next((f for f in files if f.get("primary")),None) or (files[0] if files else None)
            if not target: self.after(0,lambda:st_v.set("No files")); return
            url=target["url"]; fn=target.get("filename",url.split("/")[-1])
            dest=os.path.join(plugins_dir,fn)
            http_download(url,dest,lambda d,t:self.after(0,lambda:st_v.set(f"⬇ {fn}  {int(d/t*100)}%")))
            self.after(0,lambda:st_v.set(f"✓ {fn}"))
            self.after(0,lambda:messagebox.showinfo("Done",f"Saved:\n{plugins_dir}",parent=win))
        except Exception as ex: self.after(0,lambda:st_v.set(f"✗ {ex}"))

    # ══════════════════════════════════════════════════════════════════════
    #  MODRINTH PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _build_modrinth_page(self):
        p=_pal()
        frame=ctk.CTkFrame(self.content,corner_radius=0,fg_color=p["bg"])
        frame.grid_columnconfigure(0,weight=1); frame.grid_rowconfigure(1,weight=1)

        # Top bar
        top=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=52)
        top.grid(row=0,column=0,sticky="ew"); top.grid_propagate(False)
        top.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(top,text=self._("modrinth_t"),font=ctk.CTkFont(size=16,weight="bold"),
                     text_color=self._accent).grid(row=0,column=0,padx=20,pady=12)
        sf=ctk.CTkFrame(top,fg_color="transparent"); sf.grid(row=0,column=1,sticky="ew",padx=(0,14))
        sf.columnconfigure(0,weight=1)
        self.mr_qv=ctk.StringVar()
        qe=ctk.CTkEntry(sf,textvariable=self.mr_qv,placeholder_text=self._("hint"),
                         corner_radius=8,height=36)
        qe.grid(row=0,column=0,sticky="ew",padx=(0,8))
        qe.bind("<Return>",lambda e:self._mr_search())
        self._btn(sf,self._("search"),self._mr_search,"acc").grid(row=0,column=1)

        # Filter bar
        fbar=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg3"],height=44)
        fbar.grid(row=1,column=0,sticky="ew"); fbar.grid_propagate(False)
        fb_inner=ctk.CTkFrame(fbar,fg_color="transparent"); fb_inner.pack(side="left",padx=14,pady=6)
        self.mr_type_var=ctk.StringVar(value="")
        self.mr_type_btns={}
        type_defs=[("",self._("all_types")),("mod",self._("mods")),("resourcepack",self._("rp")),
                   ("shader",self._("shaders")),("datapack",self._("dp")),("modpack",self._("mp"))]
        for val,lbl in type_defs:
            b=ctk.CTkButton(fb_inner,text=lbl,width=80,height=28,corner_radius=6,
                            font=ctk.CTkFont(size=11),
                            fg_color="transparent",hover_color=p["border"],
                            command=lambda v=val:self._mr_set_type(v))
            b.pack(side="left",padx=2); self.mr_type_btns[val]=b
        self._mr_set_type("")
        ctk.CTkLabel(fb_inner,text=self._("loader_lbl"),font=ctk.CTkFont(size=11),
                     text_color=p["fg2"]).pack(side="left",padx=(12,4))
        self.mr_loader_var=ctk.StringVar(value="")
        lcb=ctk.CTkComboBox(fb_inner,variable=self.mr_loader_var,width=110,
                             values=["","fabric","forge","quilt","neoforge"],state="readonly")
        lcb.pack(side="left")
        lcb.bind("<<ComboboxSelected>>",lambda e:self._mr_search())
        # instance
        ctk.CTkLabel(fb_inner,text=self._("inst_label"),font=ctk.CTkFont(size=11),
                     text_color=p["fg2"]).pack(side="left",padx=(12,4))
        self.mr_inst_var=ctk.StringVar(value="(default)")
        self.mr_inst_combo=ctk.CTkComboBox(fb_inner,variable=self.mr_inst_var,
                                            values=["(default)"]+[i["name"] for i in self.instances],
                                            state="readonly",width=130)
        self.mr_inst_combo.pack(side="left")
        # status
        self.mr_sv=ctk.StringVar(value=self._("hint"))
        ctk.CTkLabel(fbar,textvariable=self.mr_sv,font=ctk.CTkFont(size=10),
                     text_color=p["fg2"]).pack(side="right",padx=14)

        # Results
        self.mr_scroll=CTkScrollFrame2(frame)
        self.mr_scroll.grid(row=2,column=0,sticky="nsew")
        frame.grid_rowconfigure(2,weight=1)
        self.mr_scroll.grid_columnconfigure(0,weight=1)
        return frame

    def _mr_auto_search(self):
        if not self.mr_scroll.winfo_children():
            threading.Thread(target=self._mr_search_worker,daemon=True).start()

    def _mr_set_type(self,val):
        p=_pal(); acc=self._accent
        self.mr_type_var.set(val)
        for v,b in self.mr_type_btns.items():
            b.configure(fg_color=acc if v==val else "transparent",
                        text_color=("#000000" if ctk.get_appearance_mode()=="Light" else "#ffffff") if v==val else p["fg2"],
                        font=ctk.CTkFont(size=11,weight="bold") if v==val else ctk.CTkFont(size=11))

    def _mr_search(self):
        threading.Thread(target=self._mr_search_worker,daemon=True).start()

    def _mr_search_worker(self):
        p=_pal()
        self.after(0,lambda:[w.destroy() for w in self.mr_scroll.winfo_children()])
        self.after(0,lambda:self.mr_sv.set("Searching…"))
        query=self.mr_qv.get().strip(); ptype=self.mr_type_var.get()
        loader=self.mr_loader_var.get().strip()
        api=MODRINTH_API[self.settings.get("modrinth_server","original")]
        facets=[]
        if ptype: facets.append([f"project_type:{ptype}"])
        if loader: facets.append([f"categories:{loader}"])
        params={"query":query,"limit":20}
        if facets: params["facets"]=json.dumps(facets)
        try:
            data=http_get(f"{api}/search",params=params,timeout=10)
            hits=data.get("hits",[])
            srv_l="api.modrinth.com" if self.settings.get("modrinth_server")=="original" else "modrinth.black"
            self.after(0,lambda:self.mr_sv.set(f"{len(hits)} results  •  {srv_l}"))
            for item in hits: self.after(0,lambda m=item:self._mr_add_card(m))
        except OSError: self.after(0,lambda:self.mr_sv.set("No connection"))
        except Exception as ex: self.after(0,lambda:self.mr_sv.set(f"Error: {ex}"))

    def _mr_add_card(self,item):
        p=_pal()
        name=item.get("title","?"); desc=item.get("description","")[:150]
        ptype=item.get("project_type","mod"); dl=item.get("downloads",0)
        pid=item.get("project_id",item.get("slug",""))
        vers=item.get("versions",[]); latest=vers[-1] if vers else "?"
        dl_fmt=f"{dl:,}".replace(",","_").replace("_"," ")
        stripe=STRIPE_C.get(ptype,"#888")
        type_lbl={"mod":"MOD","resourcepack":"RP","shader":"SHADER","datapack":"DP","modpack":"MP"}.get(ptype,ptype.upper())

        card=ctk.CTkFrame(self.mr_scroll,corner_radius=10,
                          fg_color=p["card"],border_width=1,border_color=p["border"])
        card.pack(fill="x",padx=8,pady=4)
        ctk.CTkFrame(card,width=6,corner_radius=0,fg_color=stripe).pack(side="left",fill="y")
        body=ctk.CTkFrame(card,fg_color="transparent")
        body.pack(side="left",fill="both",expand=True,padx=12,pady=10)
        tr=ctk.CTkFrame(body,fg_color="transparent"); tr.pack(anchor="w",fill="x")
        ctk.CTkLabel(tr,text=name,font=ctk.CTkFont(size=12,weight="bold")).pack(side="left")
        ctk.CTkLabel(tr,text=f"  {type_lbl}",text_color=stripe,
                     font=ctk.CTkFont(size=10,weight="bold")).pack(side="left")
        ctk.CTkLabel(body,text=desc,font=ctk.CTkFont(size=11),text_color=p["fg2"],
                     anchor="w",justify="left",wraplength=500).pack(anchor="w",pady=(2,4))
        ctk.CTkLabel(body,text=f"⬇ {dl_fmt}  •  latest: {latest}",
                     font=ctk.CTkFont(size=10),text_color=p["fg2"]).pack(anchor="w")
        bf=ctk.CTkFrame(card,fg_color="transparent"); bf.pack(side="right",padx=12,pady=10)
        self._btn(bf,self._("download"),lambda pid=pid,pt=ptype:self._mr_pick_version(pid,pt),"acc").pack()

    def _mr_pick_version(self,pid,ptype):
        threading.Thread(target=lambda:self._mr_fetch_and_show(pid,ptype),daemon=True).start()

    def _mr_fetch_and_show(self,pid,ptype):
        api=MODRINTH_API[self.settings.get("modrinth_server","original")]
        try: vers=http_get(f"{api}/project/{pid}/version",timeout=10)
        except Exception as ex: self.after(0,lambda:messagebox.showerror(self._("err"),str(ex))); return
        if not vers: self.after(0,lambda:messagebox.showinfo("Modrinth",self._("no_files"))); return
        self.after(0,lambda:self._mr_ver_dialog(vers,ptype))

    def _mr_ver_dialog(self,versions,ptype):
        p=_pal()
        win=ctk.CTkToplevel(self); win.title(self._("choose_ver")); win.geometry("520x400"); win.grab_set()
        ctk.CTkLabel(win,text=self._("choose_ver"),font=ctk.CTkFont(size=14,weight="bold")).pack(pady=(14,8))
        lb_frame=ctk.CTkScrollableFrame(win,fg_color=p["bg3"],corner_radius=8)
        lb_frame.pack(fill="both",expand=True,padx=16,pady=(0,8))
        selected=[0]
        btns_list=[]
        for i,v in enumerate(versions):
            vn=v.get("name",v.get("version_number","?")); mc_v=", ".join(v.get("game_versions",[])[:3])
            ldr=", ".join(v.get("loaders",[]))
            btn=ctk.CTkButton(lb_frame,text=f"{vn}  •  MC {mc_v}  •  {ldr}",
                              anchor="w",corner_radius=6,fg_color="transparent",
                              hover_color=p["border"],font=ctk.CTkFont(size=11),
                              command=lambda idx=i:(
                                  [b.configure(fg_color="transparent") for b in btns_list],
                                  btns_list[idx].configure(fg_color=p["sel"]),
                                  selected.__setitem__(0,idx)))
            btn.pack(fill="x",pady=2); btns_list.append(btn)
        if btns_list: btns_list[0].configure(fg_color=p["sel"])
        br=ctk.CTkFrame(win,fg_color="transparent"); br.pack(pady=8)
        def do_dl():
            i=selected[0]; chosen=versions[i]; files=chosen.get("files",[])
            primary=next((f for f in files if f.get("primary")),None)
            target=primary or (files[0] if files else None)
            if not target: messagebox.showwarning("Modrinth",self._("no_files")); return
            url=target["url"]; fn=target.get("filename",url.split("/")[-1])
            inst_name=self.mr_inst_var.get()
            if inst_name!="(default)":
                inst=next((ii for ii in self.instances if ii["name"]==inst_name),None)
                dest_dir=(inst.get("mods_dir",inst.get("dir","")) if inst else os.path.join(MC_DIR,"mods"))
            else:
                dest_dir={"mod":os.path.join(MC_DIR,"mods"),"resourcepack":os.path.join(MC_DIR,"resourcepacks"),
                          "shader":os.path.join(MC_DIR,"shaderpacks"),"datapack":os.path.join(MC_DIR,"datapacks")
                          }.get(ptype,os.path.join(MC_DIR,"mods"))
            os.makedirs(dest_dir,exist_ok=True)
            dest=os.path.join(dest_dir,fn); win.destroy()
            threading.Thread(target=self._mr_download,args=(url,dest,fn),daemon=True).start()
        self._btn(br,self._("download"),do_dl,"acc").pack(side="left",padx=4)
        self._btn(br,self._("cancel"),win.destroy,"ghost").pack(side="left",padx=4)

    def _mr_download(self,url,dest,fn):
        def upd(d,t): self.after(0,lambda:self.mr_sv.set(f"⬇ {fn}  {int(d/t*100)}%  ({d//1024} KB)"))
        try:
            self.after(0,lambda:self.mr_sv.set(f"Downloading {fn}…"))
            http_download(url,dest,progress_cb=upd)
            self.after(0,lambda:self.mr_sv.set(f"✓ {fn} saved"))
            self.after(0,lambda:messagebox.showinfo("Downloaded!",f"{fn}\n\n{os.path.dirname(dest)}"))
        except Exception as ex: self.after(0,lambda:self.mr_sv.set(f"✗ {ex}"))

    # ══════════════════════════════════════════════════════════════════════
    #  LAN PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _build_lan_page(self):
        p=_pal()
        frame=ctk.CTkFrame(self.content,corner_radius=0,fg_color=p["bg"])
        frame.grid_columnconfigure(0,weight=1); frame.grid_rowconfigure(1,weight=1)
        hdr=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=52)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
        ctk.CTkLabel(hdr,text=self._("lan_t"),font=ctk.CTkFont(size=16,weight="bold")
                     ).pack(side="left",padx=20,pady=12)
        self._btn(hdr,self._("lan_refresh"),
                  lambda:threading.Thread(target=self._lan_scan,daemon=True).start(),"ghost"
                  ).pack(side="right",padx=16,pady=10)
        self.lan_sv=ctk.StringVar(value=self._("lan_searching"))
        ctk.CTkLabel(frame,textvariable=self.lan_sv,font=ctk.CTkFont(size=12),
                     text_color=p["fg2"]).grid(row=1,column=0,pady=6)
        self.lan_scroll=CTkScrollFrame2(frame)
        self.lan_scroll.grid(row=2,column=0,sticky="nsew")
        frame.grid_rowconfigure(2,weight=1)
        return frame

    def _lan_scan(self):
        self.after(0,lambda:self.lan_sv.set(self._("lan_searching")))
        self.after(0,lambda:[w.destroy() for w in self.lan_scroll.winfo_children()])
        found=[]
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            sock.settimeout(3.0)
            try: sock.bind(("",4445))
            except: pass
            deadline=time.time()+4.0
            while time.time()<deadline:
                try:
                    data,addr=sock.recvfrom(1024)
                    msg=data.decode("utf-8",errors="replace")
                    motd_m=re.search(r"\[MOTD\](.*?)\[/MOTD\]",msg)
                    port_m=re.search(r"\[AD\](\d+)\[/AD\]",msg)
                    if port_m:
                        entry={"ip":addr[0],"port":int(port_m.group(1)),
                               "motd":motd_m.group(1) if motd_m else "LAN Server"}
                        if entry not in found: found.append(entry)
                except socket.timeout: break
                except: break
            sock.close()
        except: pass
        self.after(0,lambda:self._lan_show(found))

    def _lan_show(self,servers):
        p=_pal()
        for w in self.lan_scroll.winfo_children(): w.destroy()
        if not servers:
            self.lan_sv.set(self._("lan_none"))
            ctk.CTkLabel(self.lan_scroll,text=self._("lan_none"),
                         text_color=p["fg2"],font=ctk.CTkFont(size=13)).pack(pady=40); return
        self.lan_sv.set(f"Found {len(servers)} server(s)")
        for srv in servers:
            card=ctk.CTkFrame(self.lan_scroll,corner_radius=10,
                              fg_color=p["card"],border_width=1,border_color=p["border"])
            card.pack(fill="x",padx=16,pady=5)
            ctk.CTkFrame(card,width=6,corner_radius=0,fg_color=self._accent).pack(side="left",fill="y")
            info=ctk.CTkFrame(card,fg_color="transparent")
            info.pack(side="left",fill="both",expand=True,padx=14,pady=10)
            ctk.CTkLabel(info,text=srv.get("motd","LAN Server"),font=ctk.CTkFont(size=13,weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info,text=f"{srv['ip']}:{srv['port']}",
                         text_color=p["fg2"],font=ctk.CTkFont(size=11)).pack(anchor="w",pady=(2,0))
            btns=ctk.CTkFrame(card,fg_color="transparent"); btns.pack(side="right",padx=10,pady=8)
            self._btn(btns,self._("btn_join"),lambda s=srv:self._lan_join(s),"acc").pack()

    def _lan_join(self,srv):
        ver=self.version_var.get() or (self.installed_versions[0] if self.installed_versions else "")
        if not ver: messagebox.showwarning(self._("warn"),self._("select_ver")); return
        if ver not in self.installed_versions:
            if messagebox.askyesno(self._("warn"),self._("install_q",ver=ver)):
                threading.Thread(target=lambda:(self._install_worker(ver),self._lan_join(srv)),daemon=True).start()
            return
        threading.Thread(target=self._launch_to_server,args=(ver,srv["ip"],str(srv["port"])),daemon=True).start()

    def _launch_to_server(self,ver,ip,port):
        acc=self._get_active_account()
        user=acc["username"] if acc else self.settings["username"]
        uuid=acc.get("uuid","00000000-0000-0000-0000-000000000000") if acc else "00000000-0000-0000-0000-000000000000"
        token=acc.get("access_token","0") if acc else "0"
        ram=self.settings["ram"]; jvm=self.settings.get("jvm_args",""); java=self._find_java() or "java"
        options={"username":user,"uuid":uuid,"token":token,
                 "jvmArguments":[f"-Xmx{ram}M",f"-Xms{min(ram,512)}M"]+(jvm.split() if jvm else []),
                 "server":ip,"port":port}
        try:
            cmd=minecraft_launcher_lib.command.get_minecraft_command(ver,MC_DIR,options)
            if cmd and cmd[0].endswith(("java","java.exe")): cmd[0]=java
            subprocess.Popen(cmd,cwd=MC_DIR)
        except Exception as ex: self.after(0,lambda:messagebox.showerror(self._("err"),str(ex)))

    # ══════════════════════════════════════════════════════════════════════
    #  SETTINGS PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _build_settings_page(self):
        p=_pal()
        frame=ctk.CTkFrame(self.content,corner_radius=0,fg_color=p["bg"])
        frame.grid_columnconfigure(0,weight=1); frame.grid_rowconfigure(1,weight=1)
        hdr=ctk.CTkFrame(frame,corner_radius=0,fg_color=p["bg2"],height=52)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
        ctk.CTkLabel(hdr,text=self._("settings_t"),font=ctk.CTkFont(size=16,weight="bold")
                     ).pack(side="left",padx=20,pady=12)

        body=CTkScrollFrame2(frame); body.grid(row=1,column=0,sticky="nsew")
        body.grid_columnconfigure(0,weight=1)

        def sec(title):
            CTkSep(body)
            ctk.CTkLabel(body,text=title,font=ctk.CTkFont(size=12,weight="bold"),
                         text_color=p["fg2"]).pack(anchor="w",padx=20,pady=(0,6))

        def row():
            r=ctk.CTkFrame(body,fg_color="transparent"); r.pack(fill="x",padx=20,pady=3); return r

        def lbl_entry(r,lbl_text,var,w=220,ph=""):
            ctk.CTkLabel(r,text=lbl_text,width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
            e=ctk.CTkEntry(r,textvariable=var,width=w,placeholder_text=ph,corner_radius=8)
            e.pack(side="left"); return e

        # ── Game ─────────────────────────────────────────────────────────
        ctk.CTkLabel(body,text="",height=8,fg_color="transparent").pack()
        r=row(); ctk.CTkLabel(r,text=self._("username_l"),width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        self.username_var=ctk.StringVar(value=self.settings["username"])
        ctk.CTkEntry(r,textvariable=self.username_var,width=220,corner_radius=8).pack(side="left")

        r=row(); ctk.CTkLabel(r,text=self._("ram_l"),width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        self.ram_var=ctk.IntVar(value=self.settings["ram"])
        self.ram_disp=ctk.CTkLabel(r,text=f"{self.settings['ram']} MB",
                                    width=70,font=ctk.CTkFont(size=12,weight="bold"),text_color=self._accent)
        self.ram_disp.pack(side="right",padx=8)
        ctk.CTkSlider(r,from_=512,to=16384,number_of_steps=31,variable=self.ram_var,
                      command=lambda v:self.ram_disp.configure(text=f"{int(v)} MB"),
                      progress_color=self._accent,width=220).pack(side="left")

        r=row(); ctk.CTkLabel(r,text=self._("jvm_l"),width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        self.jvm_var=ctk.StringVar(value=self.settings.get("jvm_args",""))
        ctk.CTkEntry(r,textvariable=self.jvm_var,width=320,corner_radius=8,
                     font=ctk.CTkFont(family="Consolas",size=11)).pack(side="left")

        sec("Language / Interface")
        r=row(); ctk.CTkLabel(r,text=self._("lang_l"),width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        self.lang_var=ctk.StringVar(value=self.settings.get("language","en"))
        ctk.CTkRadioButton(r,text="English",variable=self.lang_var,value="en").pack(side="left",padx=(0,16))
        ctk.CTkRadioButton(r,text="Русский",variable=self.lang_var,value="ru").pack(side="left")

        r=row(); ctk.CTkLabel(r,text="Theme:",width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        self.theme_var=ctk.StringVar(value=self.settings.get("theme","dark"))
        ctk.CTkComboBox(r,variable=self.theme_var,
                         values=["dark","light","midnight","forest","ocean"],
                         state="readonly",width=180).pack(side="left")

        sec(self._("accent_t"))
        r=row()
        self.accent_preview=ctk.CTkFrame(r,width=36,height=36,corner_radius=6,
                                          fg_color=self.settings.get("accent_color","#5dbb63"))
        self.accent_preview.pack(side="left",padx=(0,10))
        self.accent_hex_var=ctk.StringVar(value=self.settings.get("accent_color","#5dbb63"))
        ace=ctk.CTkEntry(r,textvariable=self.accent_hex_var,width=100,corner_radius=8); ace.pack(side="left",padx=(0,8))
        def pv(*_):
            c=self.accent_hex_var.get().strip()
            if re.match(r"^#[0-9a-fA-F]{6}$",c): self.accent_preview.configure(fg_color=c)
        self.accent_hex_var.trace_add("write",pv)
        self._btn(r,self._("pick_color"),self._pick_accent,"ghost").pack(side="left")
        # swatches
        sw=ctk.CTkFrame(body,fg_color="transparent"); sw.pack(anchor="w",padx=20,pady=(4,0))
        for c in ["#5dbb63","#3a8fd9","#e05050","#e0a020","#9b59b6","#20b0e0","#e07830","#d4a017","#e0507a","#50e0c0"]:
            b=ctk.CTkButton(sw,text="",width=24,height=24,corner_radius=6,
                            fg_color=c,hover_color=_lerp_color(c,"#ffffff",0.2),
                            command=lambda col=c:(self.accent_hex_var.set(col),self.accent_preview.configure(fg_color=col)))
            b.pack(side="left",padx=2)

        sec(self._("gradient_t"))
        r=row()
        self.gradient_var=ctk.BooleanVar(value=self.settings.get("gradient_theme",False))
        ctk.CTkCheckBox(r,text=self._("gradient_en"),variable=self.gradient_var).pack(side="left")
        r2=row()
        ctk.CTkLabel(r2,text=self._("grad_c1"),width=80,font=ctk.CTkFont(size=11),anchor="w").pack(side="left")
        self.grad_c1_var=ctk.StringVar(value=self.settings.get("gradient_colors",["#5dbb63","#3a8fd9"])[0])
        ctk.CTkEntry(r2,textvariable=self.grad_c1_var,width=100,corner_radius=8).pack(side="left",padx=(0,16))
        ctk.CTkLabel(r2,text=self._("grad_c2"),width=80,font=ctk.CTkFont(size=11),anchor="w").pack(side="left")
        self.grad_c2_var=ctk.StringVar(value=self.settings.get("gradient_colors",["#5dbb63","#3a8fd9"])[1])
        ctk.CTkEntry(r2,textvariable=self.grad_c2_var,width=100,corner_radius=8).pack(side="left")

        sec(self._("mr_server"))
        r=row()
        self.mr_srv_var=ctk.StringVar(value=self.settings.get("modrinth_server","original"))
        ctk.CTkRadioButton(r,text=self._("mr_orig")+" (api.modrinth.com)",
                           variable=self.mr_srv_var,value="original").pack(side="left",padx=(0,16))
        ctk.CTkRadioButton(r,text=self._("mr_mirror")+" (modrinth.black)",
                           variable=self.mr_srv_var,value="mirror_rf").pack(side="left")

        sec(self._("java_t"))
        r=row()
        self._btn(r,self._("java_check"),self._check_java_manual,"ghost").pack(side="left")
        self.java_path_lbl=ctk.CTkLabel(r,text="",font=ctk.CTkFont(size=10),text_color=p["fg2"])
        self.java_path_lbl.pack(side="left",padx=10)
        r2=row()
        self._btn(r2,self._("auto_dl_java"),
                  lambda:threading.Thread(target=self._download_java,daemon=True).start(),"ghost").pack(side="left")
        self.java_dl_var=ctk.StringVar(value="")
        ctk.CTkLabel(r2,textvariable=self.java_dl_var,text_color=self._accent,
                     font=ctk.CTkFont(size=10)).pack(side="left",padx=10)

        sec("Updates")
        r=row()
        ctk.CTkLabel(r,text=self._("upd_check"),width=160,anchor="w",font=ctk.CTkFont(size=12)).pack(side="left")
        self.upd_var=ctk.BooleanVar(value=self.settings.get("check_updates",True))
        ctk.CTkCheckBox(r,text="",variable=self.upd_var,width=40).pack(side="left")
        r2=row()
        self._btn(r2,"🔍  Check now",self._manual_update_check,"ghost").pack(side="left")
        self.upd_status_v=ctk.StringVar(value="")
        ctk.CTkLabel(r2,textvariable=self.upd_status_v,text_color=self._accent,
                     font=ctk.CTkFont(size=10)).pack(side="left",padx=10)

        sec("Paths")
        for lk,path in [("mc_folder",MC_DIR),("srv_folder",SERVERS_DIR)]:
            r=row()
            ctk.CTkLabel(r,text=self._(lk),width=160,anchor="w",font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(r,text=path,text_color=p["fg2"],font=ctk.CTkFont(size=10)).pack(side="left")

        ctk.CTkLabel(body,text="",height=8,fg_color="transparent").pack()
        self._btn(body,self._("save_btn"),self._save_settings,"acc").pack(padx=20,pady=(0,20),anchor="w")
        return frame

    def _pick_accent(self):
        c=colorchooser.askcolor(color=self.accent_hex_var.get(),title="Pick accent color")[1]
        if c: self.accent_hex_var.set(c); self.accent_preview.configure(fg_color=c)

    # ══════════════════════════════════════════════════════════════════════
    #  JAVA
    # ══════════════════════════════════════════════════════════════════════
    def _find_java_async(self):
        threading.Thread(target=self._find_java_bg,daemon=True).start()

    def _find_java_bg(self):
        p=self._find_java()
        if p:
            self._java_path=p
            self.after(0,lambda:self.java_status_lbl.configure(text="☕ Java found"))
        else:
            self.after(0,lambda:self.java_status_lbl.configure(text="⚠ Java not found",text_color="#e05050"))

    def _find_java(self):
        import shutil as sh
        for root,dirs,files in os.walk(JAVA_DIR):
            for f in files:
                if f in ("java","java.exe"): return os.path.join(root,f)
        jh=os.environ.get("JAVA_HOME","")
        if jh:
            for sub in ("bin/java","bin/java.exe"):
                pp=os.path.join(jh,sub)
                if os.path.exists(pp): return pp
        j=sh.which("java")
        if j: return j
        return None

    def _check_java_manual(self):
        p=self._find_java()
        try:
            if p:
                self._java_path=p; self.java_path_lbl.configure(text=p[:60]); self.java_status_lbl.configure(text="☕ Java found")
            else: self.java_path_lbl.configure(text="Not found")
        except: pass

    def _download_java(self):
        def upd(m):
            try: self.after(0,lambda:self.java_dl_var.set(m))
            except: pass
        try:
            upd(self._("java_dl",ver=21))
            os_name=JAVA_OS_MAP.get(sys.platform,"linux")
            assets=http_get(JAVA_API.format(major=21,os=os_name),timeout=15)
            if not assets: upd("No assets found"); return
            pkg=assets[0].get("binary",{}).get("package",{})
            dl_url=pkg.get("link",""); fn=pkg.get("name","jre.tar.gz")
            if not dl_url: upd("No download URL"); return
            dest=os.path.join(JAVA_DIR,fn)
            http_download(dl_url,dest,lambda d,t:upd(f"Java 21  {int(d/t*100)}%  ({d//1048576} MB)"))
            upd("Extracting…")
            if fn.endswith(".zip"):
                import zipfile
                with zipfile.ZipFile(dest) as z: z.extractall(JAVA_DIR)
            elif fn.endswith((".tar.gz",".tgz")):
                import tarfile
                with tarfile.open(dest) as tar: tar.extractall(JAVA_DIR)
            os.remove(dest); self._find_java_bg(); upd(self._("java_ok",ver=21))
        except Exception as ex: upd(f"✗ {ex}")

    # ══════════════════════════════════════════════════════════════════════
    #  UPDATE CHECK
    # ══════════════════════════════════════════════════════════════════════
    def _bg_update_check(self):
        try:
            data=http_get(GITHUB_API,timeout=8)
            tag=data.get("tag_name",""); url=data.get("html_url",GITHUB_REL); body=data.get("body","")
            if _ver_tuple(tag)>_ver_tuple(APP_VERSION):
                self._update_info=(tag,url,body); self.after(0,self._show_update_banner)
        except: pass

    def _show_update_banner(self):
        try: self.update_banner.grid(row=13,column=0,sticky="ew",padx=8,pady=(0,8))
        except: pass

    def _open_update_page(self):
        if self._update_info:
            tag,url,body=self._update_info
            if messagebox.askyesno(self._("upd_title"),
                                   self._("upd_msg",tag=tag,body=body[:300])):
                webbrowser.open(url)

    def _manual_update_check(self):
        self.upd_status_v.set(self._("checking"))
        def _do():
            try:
                data=http_get(GITHUB_API,timeout=8)
                tag=data.get("tag_name",""); url=data.get("html_url",GITHUB_REL); body=data.get("body","")
                if _ver_tuple(tag)>_ver_tuple(APP_VERSION):
                    self._update_info=(tag,url,body); self.after(0,self._show_update_banner); self.after(0,self._open_update_page)
                else: self.after(0,lambda:self.upd_status_v.set(self._("upd_no")))
            except Exception as ex: self.after(0,lambda:self.upd_status_v.set(f"Error: {ex}"))
        threading.Thread(target=_do,daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════
    #  GRADIENT ANIMATION
    # ══════════════════════════════════════════════════════════════════════
    def _anim_gradient(self):
        if not self.settings.get("gradient_theme",False): return
        cols=self.settings.get("gradient_colors",["#5dbb63","#3a8fd9"])
        t2=abs(((self._grad_t%1.0)*2)-1.0)
        blended=_lerp_color(cols[0],cols[1],t2)
        self._accent=blended
        try:
            self._logo_btn.configure(text_color=blended)
            self.progress_bar.configure(progress_color=blended)
        except: pass
        self._grad_t=(self._grad_t+0.004)%1.0
        self.after(60,self._anim_gradient)

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════
    def _btn(self,parent,text,cmd,style="ghost"):
        acc=self._accent
        if style=="acc":
            return ctk.CTkButton(parent,text=text,command=cmd,
                                  fg_color=acc,hover_color=_lerp_color(acc,"#000000",0.18),
                                  text_color="#ffffff",corner_radius=8,
                                  font=ctk.CTkFont(size=12,weight="bold"))
        else:
            p=_pal()
            return ctk.CTkButton(parent,text=text,command=cmd,
                                  fg_color=p["bg3"],hover_color=p["border"],
                                  text_color=p["fg"],corner_radius=8,
                                  font=ctk.CTkFont(size=12))

    def _log(self,msg):
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end",msg+"\n"); self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.after(0,_do)

    def _set_progress(self,val,label=""):
        self.after(0,lambda:self.progress_bar.set(val/100))
        self.after(0,lambda:self.progress_lbl.configure(text=label))

    # ══════════════════════════════════════════════════════════════════════
    #  MC VERSIONS
    # ══════════════════════════════════════════════════════════════════════
    def _load_versions_async(self):
        threading.Thread(target=self._load_versions,daemon=True).start()

    def _load_versions(self):
        self._log("Fetching Minecraft versions…")
        try:
            self.mc_versions=minecraft_launcher_lib.utils.get_version_list()
            self._filter_versions(); self._refresh_installed()
            self._log(f"Loaded {len(self.mc_versions)} versions")
        except Exception as ex: self._log(f"Error: {ex}")

    def _filter_versions(self):
        vtype=self.ver_type_var.get()
        filtered=[v["id"] for v in self.mc_versions if v["type"]==vtype]
        def _do():
            self.version_combo.configure(values=filtered)
            if filtered:
                last=self.settings.get("last_version","")
                self.version_var.set(last if last in filtered else filtered[0])
        self.after(0,_do)

    def _refresh_installed(self):
        try:
            inst=minecraft_launcher_lib.utils.get_installed_versions(MC_DIR)
            self.installed_versions=[v["id"] for v in inst]
        except: self.installed_versions=[]
        def _do():
            self.installed_lb.configure(state="normal"); self.installed_lb.delete("1.0","end")
            if self.installed_versions:
                for v in self.installed_versions: self.installed_lb.insert("end","  "+v+"\n")
            else:
                self.installed_lb.insert("end","  No installed versions\n")
            self.installed_lb.configure(state="disabled")
        self.after(0,_do)

    def _on_inst_lb_select(self,event): pass  # handled by combobox

    # ══════════════════════════════════════════════════════════════════════
    #  INSTALL / LAUNCH
    # ══════════════════════════════════════════════════════════════════════
    def _install_version(self):
        ver=self.version_var.get()
        if not ver: messagebox.showwarning(self._("warn"),self._("select_ver")); return
        threading.Thread(target=self._install_worker,args=(ver,),daemon=True).start()

    def _install_worker(self,ver,target_dir=None):
        d=target_dir or MC_DIR
        self._log(self._("installing",ver=ver)); self._set_progress(0,self._("installing",ver=ver))
        cbs={"setStatus":lambda s:self._log(f"  {s}"),
             "setProgress":lambda v:None,"setMax":lambda v:None}
        try:
            minecraft_launcher_lib.install.install_minecraft_version(ver,d,callback=cbs)
            self._log(self._("inst_ok",ver=ver)); self._set_progress(100,self._("inst_ok",ver=ver))
            self._refresh_installed()
        except Exception as ex: self._log(f"✗ {ex}"); self._set_progress(0,"Error")

    def _launch_game(self):
        ver=self.version_var.get()
        if not ver: messagebox.showwarning(self._("warn"),self._("select_ver")); return
        if ver not in self.installed_versions:
            if messagebox.askyesno("MiniLauncher",self._("install_q",ver=ver)):
                def _i(): self._install_worker(ver); self.after(0,self._launch_game)
                threading.Thread(target=_i,daemon=True).start()
            return
        threading.Thread(target=self._launch_worker,args=(ver,),daemon=True).start()

    def _launch_worker(self,ver):
        acc=self._get_active_account()
        user  = acc["username"] if acc else self.settings["username"]
        uuid  = acc.get("uuid","00000000-0000-0000-0000-000000000000") if acc else "00000000-0000-0000-0000-000000000000"
        token = acc.get("access_token","0") if acc else "0"
        ram=self.settings["ram"]; jvm=self.settings.get("jvm_args",""); java=self._find_java() or "java"
        inst_name=self.play_inst_var.get()
        inst=next((i for i in self.instances if i["name"]==inst_name),None) if inst_name!="(default)" else None
        game_dir=inst["dir"] if inst else MC_DIR
        self._log(self._("launching",ver=ver,user=user)); self._set_progress(50,"Preparing…")
        options={"username":user,"uuid":uuid,"token":token,
                 "jvmArguments":[f"-Xmx{ram}M",f"-Xms{min(ram,512)}M"]+(jvm.split() if jvm else [])}
        try:
            cmd=minecraft_launcher_lib.command.get_minecraft_command(ver,game_dir,options)
            if cmd and cmd[0].endswith(("java","java.exe")): cmd[0]=java
        except Exception as ex: self._log(f"✗ {ex}"); self._set_progress(0,""); return
        self._log("Launching…"); self._set_progress(100,"Game running!")
        self.settings["last_version"]=ver; _save_json(SETTINGS_F,self.settings)
        try:
            proc=subprocess.Popen(cmd,cwd=game_dir,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:
                line=line.rstrip()
                if line: self._log(f"[MC] {line}")
            proc.wait(); self._log(self._("closed",code=proc.returncode)); self._set_progress(0,"Game closed")
        except FileNotFoundError: self._log("✗ Java not found!"); messagebox.showerror(self._("err"),self._("java_err")); self._set_progress(0,"")
        except Exception as ex: self._log(f"✗ {ex}"); self._set_progress(0,"")

    # ══════════════════════════════════════════════════════════════════════
    #  SAVE / TOGGLE
    # ══════════════════════════════════════════════════════════════════════
    def _save_settings(self):
        old_lang=self.settings.get("language","en")
        self.settings["username"]        = self.username_var.get().strip() or "Player"
        self.settings["ram"]             = self.ram_var.get()
        self.settings["jvm_args"]        = self.jvm_var.get().strip()
        self.settings["modrinth_server"] = self.mr_srv_var.get()
        self.settings["check_updates"]   = self.upd_var.get()
        self.settings["language"]        = self.lang_var.get()
        self.settings["theme"]           = self.theme_var.get()
        self.settings["accent_color"]    = self.accent_hex_var.get().strip()
        self.settings["gradient_theme"]  = self.gradient_var.get()
        self.settings["gradient_colors"] = [self.grad_c1_var.get().strip(),
                                             self.grad_c2_var.get().strip()]
        _save_json(SETTINGS_F,self.settings)
        messagebox.showinfo("MiniLauncher",self._("saved"))
        if self.settings["language"]!=old_lang: messagebox.showinfo("MiniLauncher",self._("restart_t"))
        if self.settings["gradient_theme"] and self._grad_t==0.0: self.after(100,self._anim_gradient)

    def _toggle_theme(self):
        themes=["dark","light","midnight","forest","ocean"]
        cur=self.settings.get("theme","dark")
        nxt=themes[(themes.index(cur)+1)%len(themes)] if cur in themes else "dark"
        self.settings["theme"]=nxt; _save_json(SETTINGS_F,self.settings)
        messagebox.showinfo("MiniLauncher",f"Theme: {nxt}\n{self._('restart_t')}")


if __name__=="__main__":
    app=MiniLauncher()
    app.mainloop()
