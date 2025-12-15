# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['top_window.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui/*.py', 'gui'),
        ('gui/*.png', 'gui'),
        ('gui/*.ico', 'gui'),
        ('*.ico', '.'),
        ('*.png', '.')
    ],
    hiddenimports=['gui.window_manager', 'gui.modern_ui', 'win32api', 'win32con', 'win32gui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TopWindow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['top_window_icon.ico'],
)