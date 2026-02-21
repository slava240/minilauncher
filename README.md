# ⛏ MiniLauncher

A simple Minecraft launcher with the Modrinth browser.

## Starting from source

```
pip install -r requirements.txt
python launcher.py
```

---

## Build in .exe (Windows)

### Method 1 is via build.bat (recommended)

Double-click on `build.bat`

### Method 2 — via .the spec file

Double-click on `build_spec.bat`

---

## If the exe does not start ("Sequence number not found in DLL")

This error occurs due to a Python/DLL conflict. Decisions in order:

### Solution 1 — use official Python (most common)

1. Uninstall Python if it is installed through the Microsoft Store, Conda or winget
2. Download Python **3.11** from the official website: https://www.python.org/downloads/release/python-3119 /
- Select: `Windows installer (64-bit)'
- Check the box **"Add Python to PATH" during installation**
3. Open a new cmd and reassemble:
   ```
   pip install minecraft-launcher-lib requests pyinstaller
   build.bat
   ```

### Solution 2 — collect with the --collect-all flag

```
pyinstaller --onefile --windowed --name MiniLauncher --collect-all minecraft_launcher_lib --collect-all requests --upx-dir="" launcher.py
```

### Solution 3 — run as .py (no exe needed)

```
pip install -r requirements.txt
python launcher.py
```

---

## Folder structure after startup

```
MiniLauncher/
├── launcher.py
├── requirements.txt
├── build.bat # exe build (method 1)
├── build_spec.bat # exe build (method 2)
├── MiniLauncher.spec # PyInstaller config
├── settings.json #
is created automatically.── minecraft/
    ├── versions/
    ├── assets/
    ├── mods/           # Downloaded mods
    ├── resourcepacks/
    ├── shaderpacks/
    └── datapacks/
```

## Requirements

- Python 3.9–3.12 (official from python.org )
- Java 21 to run Minecraft: https://adoptium.net
