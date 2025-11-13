# fileorg/cli/progress_display.py
import sys
import time


class ProgressDisplay:
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
