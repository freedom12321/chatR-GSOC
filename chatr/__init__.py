"""ChatR: An intelligent, local assistant for R programmers."""

__version__ = "0.1.0"
__author__ = "ChatR Team"

from .core.config import ChatRConfig
from .core.assistant import ChatRAssistant

__all__ = ["ChatRConfig", "ChatRAssistant"]