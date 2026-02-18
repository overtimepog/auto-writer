import time
from threading import Event, Lock
from typing import Callable
from pynput.keyboard import Key, Controller

from src.engine.delay_model import DelayModel
from src.engine.typo_generator import TypoGenerator
from src.config.config_store import AppSettings


class TypingEngine:
    """Core typing simulation engine. Runs on a worker thread."""

    def __init__(self, settings: AppSettings,
                 on_status_change: Callable[[str], None]):
        """
        settings: AppSettings with typing parameters
        on_status_change: callback for status updates ("typing", "idle", "cancelled")
        """
        self._controller = Controller()
        self._cancel_event = Event()
        self._typing_lock = Lock()  # Prevent concurrent typing sessions
        self._on_status_change = on_status_change
        self.update_settings(settings)

    def update_settings(self, settings: AppSettings) -> None:
        """Update delay model and typo generator from new settings."""
        self._delay_model = DelayModel(
            wpm=settings.typing_speed_wpm,
            variance=settings.speed_variance,
            min_ms=settings.min_delay_ms,
            max_ms=settings.max_delay_ms
        )
        self._typo_generator = TypoGenerator(typo_rate=settings.typo_rate)

    def run(self, text: str) -> None:
        """Main typing loop. Call from a worker thread.

        For each character:
        1. Check cancel_event - if set, stop
        2. Handle special chars (newline -> Key.enter, tab -> Key.tab)
        3. For alpha chars: maybe inject typo (type wrong key, delay, backspace, delay)
        4. Type the correct character
        5. Sleep gaussian-distributed delay
        """
        if not self._typing_lock.acquire(blocking=False):
            return  # Already typing, ignore

        try:
            self._cancel_event.clear()
            self._on_status_change("typing")

            for char in text:
                if self._cancel_event.is_set():
                    self._on_status_change("cancelled")
                    return

                if char == '\n':
                    self._controller.press(Key.enter)
                    self._controller.release(Key.enter)
                elif char == '\t':
                    self._controller.press(Key.tab)
                    self._controller.release(Key.tab)
                else:
                    # Maybe inject a typo for alpha characters
                    if char.isalpha() and self._typo_generator.should_typo():
                        typo_char = self._typo_generator.get_typo_char(char)
                        if typo_char is not None:
                            self._type_char(typo_char)
                            time.sleep(self._delay_model.next_delay())
                            # Backspace to correct
                            self._controller.press(Key.backspace)
                            self._controller.release(Key.backspace)
                            time.sleep(self._delay_model.next_delay() * 0.5)

                    self._type_char(char)

                time.sleep(self._delay_model.next_delay())

            self._on_status_change("idle")
        finally:
            self._typing_lock.release()

    def cancel(self) -> None:
        """Signal the typing loop to stop."""
        self._cancel_event.set()

    def _type_char(self, char: str) -> None:
        """Type a single character using pynput controller."""
        self._controller.type(char)
