@echo off
echo === MiniLauncher Build (spec metod) ===
echo.

pip install minecraft-launcher-lib requests pyinstaller --upgrade

if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo Building with .spec file...
pyinstaller MiniLauncher.spec

if exist dist\MiniLauncher.exe (
    echo.
    echo === OK: dist\MiniLauncher.exe ===
) else (
    echo ERROR: check logs
)
pause
