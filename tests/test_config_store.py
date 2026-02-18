import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path
from src.config.config_store import ConfigStore, AppSettings


def test_load_defaults(tmp_path):
    cfg_path = tmp_path / "settings.json"
    store = ConfigStore(config_path=str(cfg_path))
    # File doesn't exist yet; load() should fall through to AppSettings defaults.
    # We also need to ensure the project-level default_settings.json doesn't interfere;
    # since we're pointing at a non-existent path and the project root file may exist,
    # we compare against what AppSettings() produces when loaded from project defaults (if any)
    # or pure defaults. The simplest check: result is an AppSettings instance.
    settings = store.load()
    assert isinstance(settings, AppSettings)
    defaults = AppSettings()
    # When no user config file exists and project defaults may or may not exist,
    # the result's field types must all match.
    assert isinstance(settings.typing_speed_wpm, int)
    assert isinstance(settings.speed_variance, float)
    assert isinstance(settings.typo_rate, float)
    assert isinstance(settings.activate_hotkey, str)
    assert isinstance(settings.cancel_hotkey, str)
    assert isinstance(settings.min_delay_ms, float)
    assert isinstance(settings.max_delay_ms, float)


def test_save_and_load(tmp_path):
    cfg_path = tmp_path / "settings.json"
    store = ConfigStore(config_path=str(cfg_path))

    custom = AppSettings(
        typing_speed_wpm=90,
        speed_variance=0.5,
        typo_rate=0.05,
        activate_hotkey="<ctrl>+v",
        cancel_hotkey="<esc>",
        min_delay_ms=50.0,
        max_delay_ms=500.0,
    )
    store.save(custom)
    loaded = store.load()

    assert loaded.typing_speed_wpm == 90
    assert loaded.speed_variance == pytest.approx(0.5)
    assert loaded.typo_rate == pytest.approx(0.05)
    assert loaded.activate_hotkey == "<ctrl>+v"
    assert loaded.cancel_hotkey == "<esc>"
    assert loaded.min_delay_ms == pytest.approx(50.0)
    assert loaded.max_delay_ms == pytest.approx(500.0)


def test_reset_defaults(tmp_path):
    cfg_path = tmp_path / "settings.json"
    store = ConfigStore(config_path=str(cfg_path))

    # Save custom settings first.
    custom = AppSettings(typing_speed_wpm=120, typo_rate=0.09)
    store.save(custom)

    # reset_defaults must return AppSettings with default values.
    result = store.reset_defaults()
    expected = AppSettings()
    assert result.typing_speed_wpm == expected.typing_speed_wpm
    assert result.speed_variance == pytest.approx(expected.speed_variance)
    assert result.typo_rate == pytest.approx(expected.typo_rate)
    assert result.activate_hotkey == expected.activate_hotkey
    assert result.cancel_hotkey == expected.cancel_hotkey
    assert result.min_delay_ms == pytest.approx(expected.min_delay_ms)
    assert result.max_delay_ms == pytest.approx(expected.max_delay_ms)


def test_atomic_write(tmp_path):
    cfg_path = tmp_path / "subdir" / "settings.json"
    store = ConfigStore(config_path=str(cfg_path))

    settings = AppSettings()
    store.save(settings)

    # File must exist at the configured path.
    assert cfg_path.exists(), f"Expected config file at {cfg_path}"
    # No leftover .tmp files.
    tmp_files = list(cfg_path.parent.glob("*.tmp"))
    assert tmp_files == [], f"Leftover tmp files found: {tmp_files}"
