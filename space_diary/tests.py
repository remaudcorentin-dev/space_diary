"""Utility for testing code"""
from unittest import mock
import atexit


_monkey_patches = []


def monkey_patch():
    """Monkey patch tasks."""

    _monkey_patches.append(mock.patch("space_diary.tasks.add_api_operation"))

    [patch.start() for patch in _monkey_patches]

    def stop_patches():
        def stop_patch(patch):
            try:
                patch.stop()
            except RuntimeError:
                pass
        [stop_patch(patch) for patch in _monkey_patches]

    atexit.register(stop_patches)


def stop_monkey_patch():
    """Cancel all patches."""
    [patch.stop() for patch in _monkey_patches]
