# PyInstaller spec for the Patient Management System.
# Build with:  pyinstaller PatientManagement.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = (
    collect_submodules("matplotlib.backends")
    + collect_submodules("reportlab")
    + collect_submodules("ttkbootstrap")
)
datas = collect_data_files("ttkbootstrap")

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PatientManagement",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
