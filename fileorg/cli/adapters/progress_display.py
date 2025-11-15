# fileorg/cli/progress_display.py
import sys
import time

from fileorg.cli.ports import ProgressPort


class ProgressDisplay(ProgressPort):
    """Command-line interface implementation of a progress display.

    This class provides methods to update progress messages in the terminal
    and indicate completion of tasks. Designed to be used as a ProgressPort
    adapter in a hexagonal architecture.

    Attributes:
        last_message (str | None): Stores the last message displayed to the user.
    """

    def __init__(self):
        self.last_message = None

    def update(self, message: str):
        sys.stdout.write(f"\r{message.ljust(60)}")
        sys.stdout.flush()
        self.last_message = message
        time.sleep(0.2)  # Simulate delay (can be removed)

    def done(self):
        sys.stdout.write("\rAll tasks completed!\n")
        sys.stdout.flush()
