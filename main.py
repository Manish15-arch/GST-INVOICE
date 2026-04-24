"""
Tally Invoice Generator — Main Entry Point
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from ui.app import InvoiceApp


def main():
    db = Database()
    db.initialize()
    app = InvoiceApp(db)
    app.run()


if __name__ == "__main__":
    main()
