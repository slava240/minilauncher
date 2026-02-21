# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Собираем все данные и бинарники зависимостей
mc_datas, mc_binaries, mc_hiddenimports = collect_all('minecraft_launcher_lib')
req_datas, req_binaries, req_hiddenimports = collect_all('requests')

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=mc_binaries + req_binaries,
    datas=mc_datas + req_datas,
    hiddenimports=(
        mc_hiddenimports + req_hiddenimports + [
            'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
            'tkinter.scrolledtext', 'tkinter.font',
            'urllib.request', 'urllib.parse', 'urllib.error',
            'json', 'threading', 'subprocess', 'os', 'sys',
            'certifi', 'charset_normalizer', 'idna', 'urllib3',
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'cv2', 'PyQt5', 'PyQt6', 'wx',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MiniLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX отключён — частая причина DLL ошибок
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # windowed (без консоли)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
