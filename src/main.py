#!/usr/bin/env python3
"""AutoTyper — Human-like clipboard typing tool."""

import sys
import os

# Add project root to path so 'src' package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_controller import AppController


def main():
    app = AppController()
    app.start()


if __name__ == "__main__":
    main()
