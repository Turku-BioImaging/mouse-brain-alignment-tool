# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import vispy.glsl
import vispy.io
import os
import sys
import napari_builtins

datas = [
    ("gui", "gui"),
    ("brain_atlas_files", "brain_atlas_files"),
    (os.path.dirname(vispy.glsl.__file__), os.path.join("vispy", "glsl")),
    (
        os.path.join(os.path.dirname(vispy.io.__file__), "_data"),
        os.path.join("vispy", "io", "_data"),
    ),
]
binaries = [
    (os.path.join(os.path.dirname(sys.executable), "Scripts", "napari.exe"), ".")
]
hiddenimports = [
    # "napari",
    "magicgui.backends._qtpy",
    "vispy.ext._bundled.six",
    "vispy.app.backends._pyqt5",
    "freetype",
    "imagecodecs._imagecodecs",
    "napari._event_loop",
    "napari.view_layers",
]

yaml_file = os.path.join(os.path.dirname(napari_builtins.__file__), "builtins.yaml")
plugins_data = [(yaml_file, "napari_builtins")]

tmp_ret = collect_all("napari")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


block_cipher = None


a = Analysis(
    ["analyze.py"],
    pathex=[],
    binaries=binaries,
    datas=datas
    + plugins_data
    + collect_data_files("vispy")
    + collect_data_files("napari")
    + collect_data_files("freetype"),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
splash = Splash(
    'gui\\module_2_splash.jpg',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    [],
    name="analyze-0.2.2",
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
