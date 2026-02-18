import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch
from src.clipboard.clipboard_reader import ClipboardReader, EmptyClipboardError, NonTextClipboardError


def test_read_success():
    with patch("pyperclip.paste", return_value="hello"):
        result = ClipboardReader.read()
    assert result == "hello"


def test_read_empty():
    with patch("pyperclip.paste", return_value=""):
        with pytest.raises(EmptyClipboardError):
            ClipboardReader.read()


def test_read_none():
    with patch("pyperclip.paste", return_value=None):
        with pytest.raises(EmptyClipboardError):
            ClipboardReader.read()


def test_read_exception():
    with patch("pyperclip.paste", side_effect=Exception("clipboard unavailable")):
        with pytest.raises(NonTextClipboardError):
            ClipboardReader.read()
