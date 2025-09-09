# Build configuration for PyInstaller

# Teacher executable spec
teacher_spec = """
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(SPECPATH).parent
sys.path.insert(0, str(project_root / 'src'))

block_cipher = None

a = Analysis(
    ['src/teacher/teacher_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src/common', 'src/common'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt5.sip',
        'asyncio',
        'websockets',
        'aiortc',
        'aiortc.contrib.media',
        'aiosqlite',
        'mss',
        'cv2',
        'PIL',
        'numpy',
        'qrcode',
        'zeroconf',
        'win32api',
        'win32con',
        'win32gui',
        'win32process',
        'win32security',
        'psutil',
        'qasync',
        'av',
        'fractions',
        'ctypes',
        'json',
        'sqlite3',
        'threading',
        'multiprocessing',
    ],
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Teacher',
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
    icon='assets/teacher_icon.ico' if os.path.exists('assets/teacher_icon.ico') else None,
)
"""

# Student executable spec
student_spec = """
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(SPECPATH).parent
sys.path.insert(0, str(project_root / 'src'))

block_cipher = None

a = Analysis(
    ['src/student/student_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src/common', 'src/common'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt5.sip',
        'asyncio',
        'websockets',
        'aiortc',
        'aiortc.contrib.media',
        'mss',
        'cv2',
        'PIL',
        'numpy',
        'qrcode',
        'zeroconf',
        'win32api',
        'win32con',
        'win32gui',
        'win32process',
        'win32security',
        'psutil',
        'qasync',
        'av',
        'fractions',
        'ctypes',
        'json',
        'threading',
        'multiprocessing',
    ],
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Student',
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
    icon='assets/student_icon.ico' if os.path.exists('assets/student_icon.ico') else None,
)
"""


def generate_spec_files():
    """Generate PyInstaller spec files"""
    with open('teacher.spec', 'w') as f:
        f.write(teacher_spec)
    
    with open('student.spec', 'w') as f:
        f.write(student_spec)
    
    print("Generated spec files: teacher.spec, student.spec")


if __name__ == "__main__":
    generate_spec_files()