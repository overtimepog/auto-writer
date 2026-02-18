"""HotkeyListener — a single persistent pynput Listener with swappable hotkeys.

Instead of stopping/restarting GlobalHotKeys (which crashes on macOS due to
CGEventTap teardown issues), we keep ONE Listener alive for the app's lifetime
and swap the HotKey objects when the user changes bindings.
"""

from pynput import keyboard
from typing import Callable, Optional
import threading


class HotkeyListener:
    def __init__(self, on_activate: Callable[[], None], on_cancel: Callable[[], None]):
        self._on_activate = on_activate
        self._on_cancel = on_cancel
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()

        # Current HotKey objects (swappable without restarting the listener)
        self._activate_hotkey: Optional[keyboard.HotKey] = None
        self._cancel_hotkey: Optional[keyboard.HotKey] = None

    @property
    def is_running(self) -> bool:
        return self._listener is not None and self._listener.is_alive()

    def start(self, activate_combo: str, cancel_combo: str) -> None:
        """Start the persistent keyboard listener and register initial hotkeys.

        Raises ValueError if the hotkey combo strings are invalid.
        """
        # Parse hotkeys first (raises ValueError on bad format)
        self._set_hotkeys(activate_combo, cancel_combo)

        # Start ONE listener that lives for the entire app session
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop the listener (only call on app shutdown)."""
        if self._listener is not None and self._listener.is_alive():
            self._listener.stop()
            self._listener.join(timeout=2.0)
        self._listener = None

    def rebind(self, activate_combo: str, cancel_combo: str) -> None:
        """Change hotkey bindings without restarting the listener.

        Raises ValueError if the combo strings are invalid.
        """
        with self._lock:
            self._set_hotkeys(activate_combo, cancel_combo)

    def _set_hotkeys(self, activate_combo: str, cancel_combo: str) -> None:
        """Parse and set new HotKey objects. Raises ValueError on bad format."""
        # keyboard.HotKey.parse validates the combo string - raises ValueError
        activate_keys = keyboard.HotKey.parse(activate_combo)
        cancel_keys = keyboard.HotKey.parse(cancel_combo)

        self._activate_hotkey = keyboard.HotKey(activate_keys, self._on_activate)
        self._cancel_hotkey = keyboard.HotKey(cancel_keys, self._on_cancel)

    def _canonical(self, key) -> keyboard.Key:
        """Convert key to canonical form for consistent matching."""
        if self._listener is not None:
            return self._listener.canonical(key)
        return key

    def _on_press(self, key) -> None:
        with self._lock:
            if self._activate_hotkey is not None:
                self._activate_hotkey.press(self._canonical(key))
            if self._cancel_hotkey is not None:
                self._cancel_hotkey.press(self._canonical(key))

    def _on_release(self, key) -> None:
        with self._lock:
            if self._activate_hotkey is not None:
                self._activate_hotkey.release(self._canonical(key))
            if self._cancel_hotkey is not None:
                self._cancel_hotkey.release(self._canonical(key))
