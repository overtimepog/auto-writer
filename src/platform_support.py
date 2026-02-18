"""Platform-aware constants for cross-platform support."""

import sys

IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

DEFAULT_ACTIVATE_HOTKEY = "<cmd>+<shift>+k" if IS_MACOS else "<ctrl>+<shift>+k"
DEFAULT_CANCEL_HOTKEY = "<esc>"

if IS_MACOS:
    MONOSPACE_FONT = "Menlo"
elif IS_WINDOWS:
    MONOSPACE_FONT = "Consolas"
else:
    MONOSPACE_FONT = "DejaVu Sans Mono"
