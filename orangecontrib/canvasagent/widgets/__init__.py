"""Orange widget category for Canvas Agent."""

NAME = "Canvas Agent"
DESCRIPTION = "AI-assisted Orange canvas construction."
ICON = "../icons/agent.svg"
BACKGROUND = "#f28c28"

from .OWCanvasAgent import OWCanvasAgent

__all__ = ["OWCanvasAgent"]
