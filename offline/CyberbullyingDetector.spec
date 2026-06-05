# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('..\\app', 'app'), ('..\\data\\local_dictionary.json', 'data'), ('logo.png', '.')]
binaries = []
hiddenimports = ['flask_cors', 'flask_socketio', 'flask_sqlalchemy', 'bcrypt', 'fpdf2', 'eventlet', 'numpy', 'requests', 'sqlalchemy', 'jinja2', 'markupsafe', 'itsdangerous', 'werkzeug', 'click', 'flask']
tmp_ret = collect_all('flask_sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='CyberbullyingDetector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CyberbullyingDetector',
)
