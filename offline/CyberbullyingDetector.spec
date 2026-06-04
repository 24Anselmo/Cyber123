# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\app', 'app'), ('..\\data\\local_dictionary.json', 'data'), ('logo.png', '.')],
    hiddenimports=['flask_cors', 'flask_socketio', 'flask_sqlalchemy', 'bcrypt', 'fpdf2', 'eventlet', 'numpy', 'requests', 'sqlalchemy', 'jinja2', 'markupsafe', 'itsdangerous', 'werkzeug', 'click', 'flask'],
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
