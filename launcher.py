# -*- coding: utf-8 -*-
"""
GST Billing Suite — Standalone Launcher
This is the entry point for the PyInstaller-bundled .exe
It starts the FastAPI server and opens the browser automatically.
"""
import os
import sys
import webbrowser
import threading
import time

# Fix paths for PyInstaller bundle
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# Set environment
os.environ.setdefault('JWT_SECRET', 'gst-suite-offline-key-2024')

PORT = 8000

def open_browser():
    """Wait for server to start, then open browser."""
    time.sleep(2)
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    print("=" * 52)
    print("   GST Billing Suite v3.0")
    print("   Offline Desktop Edition")
    print("=" * 52)
    print()
    print(f"  Starting server on http://localhost:{PORT}")
    print(f"  Data folder: {os.path.join(BASE_DIR, 'data')}")
    print()
    print("  DO NOT close this window while using the app.")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 52)

    # Ensure data directory exists
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and run the FastAPI app
    import uvicorn
    from api import app
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")

if __name__ == "__main__":
    main()
