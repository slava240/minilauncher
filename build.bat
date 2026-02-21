@echo off
echo === MiniLauncher Build ===
echo.

echo [1/4] Installing requraments...
pip install minecraft-launcher-lib requests pyinstaller --upgrade

echo.
echo [2/4] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist MiniLauncher.spec del MiniLauncher.spec

echo.
echo [3/4] Building exe...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "MiniLauncher" ^
  --hidden-import "minecraft_launcher_lib" ^
  --hidden-import "minecraft_launcher_lib.install" ^
  --hidden-import "minecraft_launcher_lib.command" ^
  --hidden-import "minecraft_launcher_lib.utils" ^
  --hidden-import "minecraft_launcher_lib.natives" ^
  --hidden-import "minecraft_launcher_lib.helper" ^
  --hidden-import "minecraft_launcher_lib.exceptions" ^
  --hidden-import "requests" ^
  --hidden-import "urllib.request" ^
  --hidden-import "urllib.parse" ^
  --hidden-import "tkinter" ^
  --hidden-import "tkinter.ttk" ^
  --hidden-import "tkinter.messagebox" ^
  --hidden-import "tkinter.scrolledtext" ^
  --collect-all "minecraft_launcher_lib" ^
  --collect-all "requests" ^
  launcher.py

echo.
echo [4/4] OK!
if exist dist\MiniLauncher.exe (
    echo Builded file: dist\MiniLauncher.exe
) else (
    echo ERROR: File dosent created: check logs
)
pause
