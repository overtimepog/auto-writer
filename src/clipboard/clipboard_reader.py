import pyperclip


class ClipboardError(Exception):
    """Base exception for clipboard errors."""
    pass


class EmptyClipboardError(ClipboardError):
    """Raised when clipboard is empty."""
    pass


class NonTextClipboardError(ClipboardError):
    """Raised when clipboard contains non-text content."""
    pass


class ClipboardReader:
    @staticmethod
    def read() -> str:
        """Read plain text from clipboard.

        Returns:
            str: The clipboard text content.

        Raises:
            EmptyClipboardError: If clipboard is empty or None.
            NonTextClipboardError: If clipboard content is not text.
        """
        try:
            content = pyperclip.paste()
        except Exception as e:
            raise NonTextClipboardError(f"Could not read clipboard: {e}") from e

        if content is None or content.strip() == "":
            raise EmptyClipboardError("Clipboard is empty")

        return content
