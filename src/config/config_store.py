"""ConfigStore and AppSettings for autowriter configuration management."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.platform_support import DEFAULT_ACTIVATE_HOTKEY, DEFAULT_CANCEL_HOTKEY


@dataclass
class AppSettings:
    """Application settings with typed fields and sensible defaults."""

    typing_speed_wpm: int = 70       # range 30-120
    speed_variance: float = 0.3      # range 0.0-1.0
    typo_rate: float = 0.015         # range 0.0-0.10
    activate_hotkey: str = field(default_factory=lambda: DEFAULT_ACTIVATE_HOTKEY)
    cancel_hotkey: str = field(default_factory=lambda: DEFAULT_CANCEL_HOTKEY)
    min_delay_ms: float = 20.0
    max_delay_ms: float = 300.0

    def __post_init__(self):
        """Validate and clamp settings to safe ranges."""
        self.typing_speed_wpm = max(30, min(120, int(self.typing_speed_wpm)))
        self.speed_variance = max(0.0, min(1.0, float(self.speed_variance)))
        self.typo_rate = max(0.0, min(0.10, float(self.typo_rate)))
        self.min_delay_ms = max(1.0, float(self.min_delay_ms))
        self.max_delay_ms = max(self.min_delay_ms, float(self.max_delay_ms))
        if not isinstance(self.activate_hotkey, str) or not self.activate_hotkey.strip():
            self.activate_hotkey = DEFAULT_ACTIVATE_HOTKEY
        if not isinstance(self.cancel_hotkey, str) or not self.cancel_hotkey.strip():
            self.cancel_hotkey = DEFAULT_CANCEL_HOTKEY


def _project_root() -> Path:
    """Return the project root directory (two levels up from this file)."""
    return Path(__file__).parent.parent.parent


class ConfigStore:
    """Manages persistent storage of AppSettings as JSON."""

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "autotyper" / "settings.json"

    def __init__(self, config_path: str = None) -> None:
        if config_path is None:
            self.config_path = self.DEFAULT_CONFIG_PATH
        else:
            self.config_path = Path(config_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> AppSettings:
        """Load settings from JSON.

        Resolution order:
        1. User config file (self.config_path)
        2. Project-level config/default_settings.json
        3. AppSettings dataclass defaults
        """
        if self.config_path.exists():
            return self._read_settings(self.config_path)

        project_defaults = _project_root() / "config" / "default_settings.json"
        if project_defaults.exists():
            return self._read_settings(project_defaults)

        return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """Write settings to disk atomically using write-temp-then-rename."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(settings)
        dir_ = self.config_path.parent

        # Write to a temp file in the same directory, then rename for atomicity.
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=4)
                fh.write("\n")
            os.replace(tmp_path, self.config_path)
        except Exception:
            # Clean up temp file on failure.
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def reset_defaults(self) -> AppSettings:
        """Return a fresh AppSettings with defaults and persist it."""
        settings = AppSettings()
        self.save(settings)
        return settings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_settings(path: Path) -> AppSettings:
        """Parse a JSON file into an AppSettings, ignoring unknown keys."""
        with path.open("r", encoding="utf-8") as fh:
            data: dict = json.load(fh)

        # Only pass keys that AppSettings actually accepts.
        valid_fields = {f.name for f in AppSettings.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return AppSettings(**filtered)
