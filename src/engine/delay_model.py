import random


class DelayModel:
    def __init__(self, wpm: int, variance: float, min_ms: float, max_ms: float):
        """
        wpm: words per minute (30-120)
        variance: 0.0-1.0, multiplied by mean to get stddev
        min_ms: minimum delay floor in milliseconds
        max_ms: maximum delay ceiling in milliseconds
        """
        self.mean_ms = self.wpm_to_mean_delay_ms(wpm)
        self.stddev_ms = self.mean_ms * variance
        self.min_ms = min_ms
        self.max_ms = max_ms

    def next_delay(self) -> float:
        """Returns next inter-keystroke delay in SECONDS.
        Uses random.gauss(mean, stddev) clamped to [min_ms, max_ms], then converts to seconds."""
        delay_ms = random.gauss(self.mean_ms, self.stddev_ms)
        delay_ms = max(self.min_ms, min(self.max_ms, delay_ms))
        return delay_ms / 1000.0

    @staticmethod
    def wpm_to_mean_delay_ms(wpm: int) -> float:
        """Converts WPM to mean inter-keystroke delay in milliseconds.
        Formula: (60000 / wpm) / 5 (assuming average word = 5 characters)"""
        return (60000.0 / wpm) / 5.0
