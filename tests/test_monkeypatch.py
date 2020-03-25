"""Test monkey patching."""
from unittest import TestCase
from unittest.mock import MagicMock
from space_diary.tests import monkey_patch, stop_monkey_patch


class MonkeyTestCase(TestCase):
    """Test monkey patching."""

    def test_monkey_patching(self):
        """Test monkey patching."""
        monkey_patch()

        from space_diary.tasks import add_api_operation
        self.assertTrue(isinstance(add_api_operation, MagicMock))

        stop_monkey_patch()
