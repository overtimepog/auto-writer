"""AppController — orchestrator that wires all AutoTyper modules together."""

import threading

from src.config.config_store import ConfigStore, AppSettings
from src.platform_support import DEFAULT_ACTIVATE_HOTKEY
from src.clipboard.clipboard_reader import (
    ClipboardReader,
    EmptyClipboardError,
    NonTextClipboardError,
)
from src.hotkey.hotkey_listener import HotkeyListener
from src.engine.typing_engine import TypingEngine
from src.gui.main_window import MainWindow
from src.permissions.accessibility import AccessibilityChecker


class AppController:
    """Orchestrator connecting all AutoTyper modules."""

    def __init__(self):
        # Load config
        self._config_store = ConfigStore()
        self._settings = self._config_store.load()

        # Create typing engine (status changes go to GUI via thread-safe method)
        self._engine = TypingEngine(
            settings=self._settings,
            on_status_change=self._on_status_change,
        )

        # Create hotkey listener
        self._hotkey_listener = HotkeyListener(
            on_activate=self._on_activate,
            on_cancel=self._on_cancel,
        )

        # Create GUI (must be last since it refs settings)
        self._gui = MainWindow(
            settings=self._settings,
            on_settings_changed=self._on_settings_changed,
            on_close=self._on_close,
        )


    def start(self):
        """Start the application. Starts hotkeys, runs GUI."""
        # Try to start hotkey listener
        try:
            self._hotkey_listener.start(
                self._settings.activate_hotkey,
                self._settings.cancel_hotkey,
            )
        except Exception:
            # Hotkeys failed - likely missing accessibility permissions
            self._gui.show_error(
                AccessibilityChecker.get_permission_error_message()
            )
            AccessibilityChecker.open_accessibility_prefs()

        # Run GUI mainloop (blocks until window closed)
        self._gui.run()

    def _on_activate(self):
        """Called by HotkeyListener when activate hotkey pressed."""
        try:
            text = ClipboardReader.read()
        except EmptyClipboardError:
            self._gui.show_error("Clipboard is empty. Copy some text first.")
            return
        except NonTextClipboardError as e:
            self._gui.show_error(f"Cannot read clipboard: {e}")
            return

        # Spawn typing on worker thread
        thread = threading.Thread(target=self._engine.run, args=(text,), daemon=True)
        thread.start()

    def _on_cancel(self):
        """Called by HotkeyListener when cancel hotkey pressed."""
        self._engine.cancel()

    def _on_status_change(self, status: str):
        """Called by TypingEngine. Forward to GUI (thread-safe)."""
        self._gui.set_status(status)

    def _on_settings_changed(self, new_settings: AppSettings):
        """Called by GUI when user changes settings."""
        old_settings = self._settings
        self._settings = new_settings
        self._config_store.save(new_settings)
        self._engine.update_settings(new_settings)

        # Only rebind hotkeys if they actually changed
        if (new_settings.activate_hotkey != old_settings.activate_hotkey
                or new_settings.cancel_hotkey != old_settings.cancel_hotkey):
            try:
                self._hotkey_listener.rebind(
                    new_settings.activate_hotkey,
                    new_settings.cancel_hotkey,
                )
            except (ValueError, KeyError) as e:
                self._gui.show_error(
                    f"Invalid hotkey format: {e}\n\n"
                    f"Use pynput format like {DEFAULT_ACTIVATE_HOTKEY}\n"
                    "Hotkeys reverted to previous values."
                )
                # Revert hotkey settings to the old working values
                self._settings = AppSettings(
                    typing_speed_wpm=new_settings.typing_speed_wpm,
                    speed_variance=new_settings.speed_variance,
                    typo_rate=new_settings.typo_rate,
                    activate_hotkey=old_settings.activate_hotkey,
                    cancel_hotkey=old_settings.cancel_hotkey,
                    min_delay_ms=new_settings.min_delay_ms,
                    max_delay_ms=new_settings.max_delay_ms,
                )
                # Re-start with old hotkeys
                try:
                    self._hotkey_listener.rebind(
                        old_settings.activate_hotkey,
                        old_settings.cancel_hotkey,
                    )
                except Exception:
                    pass

    def _on_close(self):
        """Called when GUI window is closed."""
        self._hotkey_listener.stop()
