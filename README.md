# ⛏ MiniLauncher

Простой Minecraft лаунчер с браузером Modrinth.

## Запуск из исходников

```
pip install -r requirements.txt
python launcher.py
```

---

## Сборка в .exe (Windows)

### Способ 1 — через build.bat (рекомендуется)

Двойной клик на `build.bat`

### Способ 2 — через .spec файл

Двойной клик на `build_spec.bat`

---

## Если exe не запускается ("Порядковый номер не найден в DLL")

Эта ошибка возникает из-за конфликта Python/DLL. Решения по порядку:

### Решение 1 — использовать официальный Python (самое частое)

1. Удали Python если он установлен через Microsoft Store, Conda или winget
2. Скачай Python **3.11** с официального сайта: https://www.python.org/downloads/release/python-3119/
   - Выбери: `Windows installer (64-bit)`
   - При установке поставь галочку **"Add Python to PATH"**
3. Открой новый cmd и собери заново:
   ```
   pip install minecraft-launcher-lib requests pyinstaller
   build.bat
   ```

### Решение 2 — собрать с флагом --collect-all

```
pyinstaller --onefile --windowed --name MiniLauncher --collect-all minecraft_launcher_lib --collect-all requests --upx-dir="" launcher.py
```

### Решение 3 — запускать как .py (не нужен exe)

```
pip install -r requirements.txt
python launcher.py
```

---

## Структура папок после запуска

```
MiniLauncher/
├── launcher.py
├── requirements.txt
├── build.bat           # Сборка exe (способ 1)
├── build_spec.bat      # Сборка exe (способ 2)
├── MiniLauncher.spec   # Конфиг PyInstaller
├── settings.json       # Создаётся автоматически
└── minecraft/
    ├── versions/
    ├── assets/
    ├── mods/           # Скачанные моды
    ├── resourcepacks/
    ├── shaderpacks/
    └── datapacks/
```

## Требования

- Python 3.9–3.12 (официальный с python.org)
- Java 21 для запуска Minecraft: https://adoptium.net
