"""macOS Accessibility permission utilities.

Uses a practical approach: try to create a pynput listener and see if it works,
rather than fragile ctypes calls to CoreFoundation APIs.
"""

import subprocess
import sys


class AccessibilityChecker:
    @staticmethod
    def is_accessible() -> bool:
        """Check if keyboard monitoring is likely to work.

        Attempts to create a pynput keyboard listener briefly.
        Returns True if it starts without error, False otherwise.
        """
        if sys.platform != "darwin":
            return True

        try:
            from pynput import keyboard

            # Try to create a listener - this will fail quickly
            # if accessibility permissions are not granted.
            listener = keyboard.Listener(on_press=lambda k: False)
            listener.daemon = True
            listener.start()
            listener.join(timeout=0.5)
            # If we got here without error, permissions are likely OK
            # (the listener stopped because our on_press returned False)
            return True
        except Exception:
            return False

    @staticmethod
    def open_accessibility_prefs() -> None:
        """Open macOS System Settings to the Accessibility pane."""
        if sys.platform != "darwin":
            return
        try:
            subprocess.run(
                [
                    "open",
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
                ],
                check=True,
            )
        except Exception:
            pass
