import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.engine.delay_model import DelayModel


def test_wpm_to_mean_delay_ms():
    # Formula: (60000 / wpm) / 5
    assert DelayModel.wpm_to_mean_delay_ms(60) == pytest.approx(200.0)
    assert DelayModel.wpm_to_mean_delay_ms(120) == pytest.approx(100.0)
    assert DelayModel.wpm_to_mean_delay_ms(30) == pytest.approx(400.0)
    assert DelayModel.wpm_to_mean_delay_ms(70) == pytest.approx(60000.0 / 70 / 5)


def test_next_delay_returns_seconds():
    model = DelayModel(wpm=60, variance=0.3, min_ms=20.0, max_ms=300.0)
    for _ in range(50):
        delay = model.next_delay()
        assert delay > 0, "delay must be positive"
        assert delay <= 1.0, "delay must not be unreasonably large (max 300ms = 0.3s)"


def test_next_delay_clamping():
    model = DelayModel(wpm=60, variance=5.0, min_ms=100.0, max_ms=200.0)
    for _ in range(200):
        delay = model.next_delay()
        assert delay >= 0.1, f"delay {delay} below min 0.1s"
        assert delay <= 0.2, f"delay {delay} above max 0.2s"


def test_variance_zero():
    model = DelayModel(wpm=60, variance=0.0, min_ms=0.0, max_ms=10000.0)
    expected_ms = DelayModel.wpm_to_mean_delay_ms(60)
    expected_s = expected_ms / 1000.0
    for _ in range(20):
        delay = model.next_delay()
        assert delay == pytest.approx(expected_s, abs=1e-9)


def test_different_wpm_different_means():
    slow = DelayModel(wpm=30, variance=0.0, min_ms=0.0, max_ms=10000.0)
    fast = DelayModel(wpm=120, variance=0.0, min_ms=0.0, max_ms=10000.0)
    assert slow.next_delay() > fast.next_delay(), "slower WPM should produce longer delay"
