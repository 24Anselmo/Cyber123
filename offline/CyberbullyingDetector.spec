# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\app', 'app'), ('logo.png', '.'), ('..\\data\\local_dictionary.json', 'data')],
    hiddenimports=['flask', 'flask_cors', 'flask_sqlalchemy', 'sqlite3', 'json', 'threading', 'logging', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'datetime', 'os', 'sys', 're', 'time'],
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
    name='CyberbullyingDetector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
