# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for GST Billing Suite
Run: pyinstaller GSTBillingSuite.spec
"""

import os
ROOT = os.path.abspath('.')

a = Analysis(
    ['launcher.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('web/dist', 'web/dist'),
        ('database.py', '.'),
        ('invoice_engine.py', '.'),
        ('pdf_exporter.py', '.'),
        ('tally_pdf.py', '.'),
        ('tally_exporter.py', '.'),
        ('excel_exporter.py', '.'),
        ('api.py', '.'),
    ],
    hiddenimports=[
        'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan',
        'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
        'fastapi', 'fastapi.applications', 'fastapi.routing', 'fastapi.middleware',
        'fastapi.middleware.cors', 'fastapi.middleware.asyncexitstack',
        'fastapi.responses', 'fastapi.staticfiles',
        'starlette', 'starlette.applications', 'starlette.routing',
        'starlette.middleware', 'starlette.middleware.cors',
        'starlette.middleware.errors', 'starlette.middleware.exceptions',
        'starlette.responses', 'starlette.staticfiles', 'starlette.concurrency',
        'pydantic', 'pydantic.fields',
        'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes',
        'reportlab.lib.colors', 'reportlab.lib.units', 'reportlab.lib.styles',
        'reportlab.lib.enums', 'reportlab.platypus', 'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts', 'reportlab.pdfbase.pdfmetrics',
        'num2words', 'sqlite3', 'email.mime.multipart',
        'h11', 'anyio', 'sniffio', 'httptools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'tkcalendar', 'matplotlib', 'numpy', 'pandas'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GSTBillingSuite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GSTBillingSuite',
)
