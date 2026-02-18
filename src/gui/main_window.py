"""MainWindow — the top-level application window for AutoTyper."""

from __future__ import annotations

from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from src.config.config_store import AppSettings
from src.gui.settings_panel import SettingsPanel


# Apply appearance before any widget is created.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Status configuration
# ---------------------------------------------------------------------------

_STATUS_CONFIG: dict[str, dict] = {
    "idle": {
        "text": "Idle",
        "color": "#10B981",      # emerald-500
        "bg": "#064E3B",         # emerald-950
        "border": "#065F46",     # emerald-900
    },
    "typing": {
        "text": "Typing...",
        "color": "#F59E0B",      # amber-400
        "bg": "#451A03",         # amber-950
        "border": "#78350F",     # amber-900
    },
    "cancelled": {
        "text": "Cancelled",
        "color": "#F87171",      # red-400
        "bg": "#450A0A",         # red-950
        "border": "#7F1D1D",     # red-900
    },
}

_WINDOW_WIDTH = 450
_WINDOW_HEIGHT = 580


class _StatusBadge(ctk.CTkFrame):
    """Large pill-shaped status indicator with a coloured dot and text."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("fg_color", "#064E3B")
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#065F46")
        super().__init__(master, **kwargs)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=24, pady=14)

        # Dot indicator
        self._dot = ctk.CTkLabel(
            inner,
            text="●",
            font=ctk.CTkFont(size=14),
            text_color="#10B981",
        )
        self._dot.pack(side="left", padx=(0, 10))

        # Status text
        self._label = ctk.CTkLabel(
            inner,
            text="Idle",
            font=ctk.CTkFont(family="Menlo", size=18, weight="bold"),
            text_color="#10B981",
        )
        self._label.pack(side="left")

    def set_state(self, status: str) -> None:
        cfg = _STATUS_CONFIG.get(status, _STATUS_CONFIG["idle"])
        self.configure(fg_color=cfg["bg"], border_color=cfg["border"])
        self._dot.configure(text_color=cfg["color"])
        self._label.configure(text=cfg["text"], text_color=cfg["color"])


class _HotkeyHint(ctk.CTkFrame):
    """Subtle single-line hint showing the current activate hotkey."""

    def __init__(self, master, hotkey: str, **kwargs):
        kwargs.setdefault("fg_color", ("#1F2937", "#1F2937"))
        kwargs.setdefault("corner_radius", 8)
        super().__init__(master, **kwargs)

        self._prefix = ctk.CTkLabel(
            self,
            text="Press",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#6B7280"),
        )
        self._prefix.pack(side="left", padx=(14, 5), pady=10)

        self._key_label = ctk.CTkLabel(
            self,
            text=self._fmt(hotkey),
            font=ctk.CTkFont(family="Menlo", size=12, weight="bold"),
            text_color=("#F59E0B", "#F59E0B"),
        )
        self._key_label.pack(side="left", pady=10)

        self._suffix = ctk.CTkLabel(
            self,
            text="to type clipboard contents",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#6B7280"),
        )
        self._suffix.pack(side="left", padx=(5, 14), pady=10)

    def update_hotkey(self, hotkey: str) -> None:
        self._key_label.configure(text=self._fmt(hotkey))

    @staticmethod
    def _fmt(hotkey: str) -> str:
        """Convert pynput-style hotkey string to a readable display form."""
        return hotkey.replace("<", "").replace(">", "").replace("+", " + ").upper()


class _Divider(ctk.CTkFrame):
    """Thin horizontal rule."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", ("#374151", "#374151"))
        kwargs.setdefault("height", 1)
        super().__init__(master, **kwargs)


class MainWindow:
    """Top-level application window.

    Parameters
    ----------
    settings:
        Initial application settings shown on launch.
    on_settings_changed:
        Called with the updated AppSettings whenever the user edits any control.
    on_close:
        Optional cleanup hook invoked when the window is closed.
    """

    def __init__(
        self,
        settings: AppSettings,
        on_settings_changed: Callable[[AppSettings], None],
        on_close: Optional[Callable[[], None]] = None,
    ):
        self._settings = settings
        self._on_settings_changed = on_settings_changed
        self._on_close = on_close

        self._root = ctk.CTk()
        self._configure_root()
        self._build_ui(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, status: str) -> None:
        """Thread-safe status update.

        Parameters
        ----------
        status:
            One of ``'idle'``, ``'typing'``, or ``'cancelled'``.
        """
        self._root.after(0, self._update_status_display, status)

    def show_error(self, message: str) -> None:
        """Display a modal error dialog."""
        # Schedule on main thread in case called from a worker thread.
        self._root.after(0, self._show_error_main_thread, message)

    def run(self) -> None:
        """Start the Tk event loop. Blocks until the window is closed."""
        self._root.mainloop()

    # ------------------------------------------------------------------
    # Internal — root configuration
    # ------------------------------------------------------------------

    def _configure_root(self) -> None:
        self._root.title("AutoTyper")
        self._root.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}")
        self._root.minsize(_WINDOW_WIDTH, _WINDOW_HEIGHT)
        self._root.resizable(True, True)

        # Centre on screen
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - _WINDOW_WIDTH) // 2
        y = (sh - _WINDOW_HEIGHT) // 2
        self._root.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}+{x}+{y}")

        self._root.protocol("WM_DELETE_WINDOW", self._handle_close)

    # ------------------------------------------------------------------
    # Internal — layout
    # ------------------------------------------------------------------

    def _build_ui(self, settings: AppSettings) -> None:
        root = self._root

        # ---- App header ------------------------------------------------
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(
            header,
            text="AutoTyper",
            font=ctk.CTkFont(family="Menlo", size=22, weight="bold"),
            text_color=("#F9FAFB", "#F9FAFB"),
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="v1.0",
            font=ctk.CTkFont(family="Menlo", size=11),
            text_color=("#6B7280", "#6B7280"),
            anchor="e",
        ).pack(side="right", pady=(6, 0))

        # ---- Status badge ----------------------------------------------
        self._status_badge = _StatusBadge(root)
        self._status_badge.pack(fill="x", padx=24, pady=(16, 0))

        # ---- Hotkey hint -----------------------------------------------
        self._hotkey_hint = _HotkeyHint(root, hotkey=settings.activate_hotkey)
        self._hotkey_hint.pack(fill="x", padx=24, pady=(10, 0))

        # ---- Divider ---------------------------------------------------
        _Divider(root).pack(fill="x", padx=24, pady=(18, 0))

        # ---- Settings label --------------------------------------------
        ctk.CTkLabel(
            root,
            text="SETTINGS",
            font=ctk.CTkFont(family="Menlo", size=10, weight="bold"),
            text_color=("#6B7280", "#6B7280"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(14, 4))

        # ---- Settings panel --------------------------------------------
        self._settings_panel = SettingsPanel(
            root,
            settings=settings,
            on_settings_changed=self._handle_settings_changed,
            fg_color=("#111827", "#111827"),
            border_width=1,
            border_color=("#374151", "#374151"),
        )
        self._settings_panel.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    # ------------------------------------------------------------------
    # Internal — callbacks
    # ------------------------------------------------------------------

    def _handle_settings_changed(self, new_settings: AppSettings) -> None:
        self._settings = new_settings
        # Keep hotkey hint in sync.
        self._hotkey_hint.update_hotkey(new_settings.activate_hotkey)
        self._on_settings_changed(new_settings)

    def _handle_close(self) -> None:
        if self._on_close is not None:
            try:
                self._on_close()
            except Exception:
                pass
        self._root.destroy()

    # ------------------------------------------------------------------
    # Internal — thread-safe helpers
    # ------------------------------------------------------------------

    def _update_status_display(self, status: str) -> None:
        """Must be called on the main thread (via root.after)."""
        self._status_badge.set_state(status)

    def _show_error_main_thread(self, message: str) -> None:
        """Must be called on the main thread (via root.after)."""
        messagebox.showerror(title="AutoTyper — Error", message=message, parent=self._root)
