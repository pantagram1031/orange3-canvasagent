from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schema import CanvasPlan


@dataclass(frozen=True)
class ModelRef:
    id: str
    label: str


@dataclass(frozen=True)
class AuthStatus:
    authenticated: bool
    message: str


class AgentBackend(Protocol):
    name: str

    def list_models(self) -> list[ModelRef]:
        raise NotImplementedError

    def run(self, prompt: str, canvas_state: dict, output_schema: dict) -> CanvasPlan:
        raise NotImplementedError

    def is_authenticated(self) -> AuthStatus:
        raise NotImplementedError

    def login(self) -> AuthStatus:
        raise NotImplementedError

