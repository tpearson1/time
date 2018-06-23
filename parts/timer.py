import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject


class Timer:
    def __init__(self, second_handler):
        self.counting = False
        self.second_handler = second_handler

    def start(self):
        if self.counting:
            # We do not want to add timer logic again
            return
        self.counting = True

        self._make_timeout()

    def _make_timeout(self):
        GObject.timeout_add_seconds(1, self._tick_second)

    def stop(self):
        self.counting = False

    def _tick_second(self):
        if not self.counting:
            # Timer was stopped so this tick should not count
            return

        self.second_handler()

        # Register for the next tick
        self._make_timeout()
