"""SettingsPanel — a CTkFrame subclass housing all user-configurable controls."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable

from src.config.config_store import AppSettings
from src.platform_support import DEFAULT_ACTIVATE_HOTKEY, IS_MACOS, MONOSPACE_FONT


_DEFAULT_SETTINGS = AppSettings()

# Hotkey capture instructions shown in the change-hotkey flow
_HOTKEY_EXAMPLE = "<cmd>+<shift>+k" if IS_MACOS else "<ctrl>+<shift>+k"
_HOTKEY_INSTRUCTIONS = (
    "To change the hotkey, edit the field directly.\n\n"
    "Use the pynput key-name format, e.g.:\n"
    f"  {_HOTKEY_EXAMPLE}\n"
    "  <ctrl>+<alt>+t\n\n"
    "Press Enter or click away to confirm."
)


class _SectionLabel(ctk.CTkLabel):
    """Small, muted section heading."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text.upper(),
            font=ctk.CTkFont(family=MONOSPACE_FONT, size=10, weight="bold"),
            text_color=("#6B7280", "#6B7280"),
            **kwargs,
        )


class _ValueLabel(ctk.CTkLabel):
    """Right-aligned numeric value display next to a slider."""

    def __init__(self, master, text: str = "", **kwargs):
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(family=MONOSPACE_FONT, size=13),
            text_color=("#F59E0B", "#F59E0B"),
            width=52,
            anchor="e",
            **kwargs,
        )


class SettingsPanel(ctk.CTkFrame):
    """Settings controls embedded in the main window."""

    def __init__(
        self,
        master,
        settings: AppSettings,
        on_settings_changed: Callable[[AppSettings], None],
        **kwargs,
    ):
        kwargs.setdefault("corner_radius", 12)
        super().__init__(master, **kwargs)

        self._settings = settings
        self._on_changed = on_settings_changed

        # Tkinter variable objects — declared before _build_ui()
        self._speed_var = ctk.IntVar(value=settings.typing_speed_wpm)
        self._typo_var = ctk.DoubleVar(value=settings.typo_rate)
        self._activate_var = ctk.StringVar(value=settings.activate_hotkey)
        self._cancel_var = ctk.StringVar(value=settings.cancel_hotkey)

        self._debounce_id = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_settings(self, settings: AppSettings) -> None:
        """Refresh every widget from a new AppSettings object."""
        self._settings = settings
        self._speed_var.set(settings.typing_speed_wpm)
        self._typo_var.set(settings.typo_rate)
        self._activate_var.set(settings.activate_hotkey)
        self._cancel_var.set(settings.cancel_hotkey)
        self._refresh_labels()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)

        pad = {"padx": 20, "pady": 0}

        # ---- Speed -------------------------------------------------------
        self._add_row_spacer(8)
        _SectionLabel(self, text="Typing Speed").grid(
            row=1, column=0, sticky="w", padx=20, pady=(0, 4)
        )

        speed_row = ctk.CTkFrame(self, fg_color="transparent")
        speed_row.grid(row=2, column=0, sticky="ew", **pad)
        speed_row.columnconfigure(0, weight=1)

        self._speed_slider = ctk.CTkSlider(
            speed_row,
            from_=30,
            to=120,
            number_of_steps=90,
            variable=self._speed_var,
            command=self._on_speed_changed,
            button_color="#F59E0B",
            button_hover_color="#D97706",
            progress_color="#F59E0B",
        )
        self._speed_slider.grid(row=0, column=0, sticky="ew", pady=2)

        self._speed_label = _ValueLabel(speed_row, text=self._fmt_speed())
        self._speed_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # ---- Typo Rate ---------------------------------------------------
        self._add_row_spacer(16, grid_row=3)
        _SectionLabel(self, text="Typo Rate").grid(
            row=4, column=0, sticky="w", padx=20, pady=(0, 4)
        )

        typo_row = ctk.CTkFrame(self, fg_color="transparent")
        typo_row.grid(row=5, column=0, sticky="ew", **pad)
        typo_row.columnconfigure(0, weight=1)

        self._typo_slider = ctk.CTkSlider(
            typo_row,
            from_=0.0,
            to=0.10,
            number_of_steps=100,
            variable=self._typo_var,
            command=self._on_typo_changed,
            button_color="#F59E0B",
            button_hover_color="#D97706",
            progress_color="#F59E0B",
        )
        self._typo_slider.grid(row=0, column=0, sticky="ew", pady=2)

        self._typo_label = _ValueLabel(typo_row, text=self._fmt_typo())
        self._typo_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # ---- Activate Hotkey --------------------------------------------
        self._add_row_spacer(16, grid_row=6)
        _SectionLabel(self, text="Activate Hotkey").grid(
            row=7, column=0, sticky="w", padx=20, pady=(0, 4)
        )

        activate_row = ctk.CTkFrame(self, fg_color="transparent")
        activate_row.grid(row=8, column=0, sticky="ew", **pad)
        activate_row.columnconfigure(0, weight=1)

        self._activate_entry = ctk.CTkEntry(
            activate_row,
            textvariable=self._activate_var,
            font=ctk.CTkFont(family=MONOSPACE_FONT, size=12),
            placeholder_text=f"e.g. {DEFAULT_ACTIVATE_HOTKEY}",
            height=32,
            corner_radius=8,
        )
        self._activate_entry.grid(row=0, column=0, sticky="ew")
        self._activate_entry.bind("<FocusOut>", lambda _e: self._schedule_notify())
        self._activate_entry.bind("<Return>", lambda _e: self._schedule_notify())

        ctk.CTkButton(
            activate_row,
            text="?",
            width=32,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#374151", "#374151"),
            hover_color=("#4B5563", "#4B5563"),
            command=self._show_hotkey_help,
        ).grid(row=0, column=1, padx=(8, 0))

        # ---- Cancel Hotkey ----------------------------------------------
        self._add_row_spacer(12, grid_row=9)
        _SectionLabel(self, text="Cancel Hotkey").grid(
            row=10, column=0, sticky="w", padx=20, pady=(0, 4)
        )

        cancel_row = ctk.CTkFrame(self, fg_color="transparent")
        cancel_row.grid(row=11, column=0, sticky="ew", **pad)
        cancel_row.columnconfigure(0, weight=1)

        self._cancel_entry = ctk.CTkEntry(
            cancel_row,
            textvariable=self._cancel_var,
            font=ctk.CTkFont(family=MONOSPACE_FONT, size=12),
            placeholder_text="e.g. <esc>",
            height=32,
            corner_radius=8,
        )
        self._cancel_entry.grid(row=0, column=0, sticky="ew")
        self._cancel_entry.bind("<FocusOut>", lambda _e: self._schedule_notify())
        self._cancel_entry.bind("<Return>", lambda _e: self._schedule_notify())

        # ---- Reset Defaults ---------------------------------------------
        self._add_row_spacer(16, grid_row=12)
        ctk.CTkButton(
            self,
            text="Reset to Defaults",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color=("#374151", "#374151"),
            hover_color=("#4B5563", "#4B5563"),
            text_color=("#9CA3AF", "#9CA3AF"),
            command=self._reset_defaults,
        ).grid(row=13, column=0, padx=20, pady=0, sticky="ew")

        self._add_row_spacer(12, grid_row=14)

    def _add_row_spacer(self, height: int, grid_row: int = 0) -> None:
        """Insert a transparent spacer frame in the given grid row."""
        ctk.CTkFrame(self, fg_color="transparent", height=height).grid(
            row=grid_row, column=0, sticky="ew"
        )

    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------

    def _fmt_speed(self) -> str:
        return f"{self._speed_var.get()} wpm"

    def _fmt_typo(self) -> str:
        pct = round(self._typo_var.get() * 100, 1)
        return f"{pct:.1f}%"

    def _refresh_labels(self) -> None:
        self._speed_label.configure(text=self._fmt_speed())
        self._typo_label.configure(text=self._fmt_typo())

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_speed_changed(self, _value) -> None:
        self._speed_label.configure(text=self._fmt_speed())
        self._notify_change()

    def _on_typo_changed(self, _value) -> None:
        self._typo_label.configure(text=self._fmt_typo())
        self._notify_change()

    def _schedule_notify(self) -> None:
        """Debounce hotkey entry changes to avoid double-fires."""
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(100, self._notify_change)

    def _notify_change(self) -> None:
        """Read widget state, construct AppSettings, fire callback."""
        self._debounce_id = None
        updated = AppSettings(
            typing_speed_wpm=int(self._speed_var.get()),
            speed_variance=self._settings.speed_variance,
            typo_rate=round(float(self._typo_var.get()), 4),
            activate_hotkey=self._activate_var.get().strip(),
            cancel_hotkey=self._cancel_var.get().strip(),
            min_delay_ms=self._settings.min_delay_ms,
            max_delay_ms=self._settings.max_delay_ms,
        )
        self._settings = updated
        self._on_changed(updated)

    def _reset_defaults(self) -> None:
        self.update_settings(_DEFAULT_SETTINGS)
        self._on_changed(_DEFAULT_SETTINGS)

    def _show_hotkey_help(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hotkey Format")
        dialog.geometry("340x220")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.focus_set()

        ctk.CTkLabel(
            dialog,
            text=_HOTKEY_INSTRUCTIONS,
            font=ctk.CTkFont(family=MONOSPACE_FONT, size=12),
            justify="left",
            wraplength=300,
        ).pack(padx=24, pady=(24, 16), anchor="w")

        ctk.CTkButton(
            dialog,
            text="Got it",
            width=100,
            command=dialog.destroy,
        ).pack(pady=(0, 16))
