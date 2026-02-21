#!/bin/bash
echo "=== MiniLauncher Build ==="

echo "[1/3] Установка зависимостей..."
pip install -r requirements.txt
pip install pyinstaller

echo "[2/3] Сборка бинарника..."
pyinstaller \
  --onefile \
  --windowed \
  --name "MiniLauncher" \
  launcher.py

echo "[3/3] Готово! Файл: dist/MiniLauncher"
