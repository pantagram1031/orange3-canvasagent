from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

from .schema import CanvasPlan


def capture_scheme_snapshot(scheme) -> bytes:
    stream = BytesIO()
    scheme.save_to(stream, pretty=True, pickle_fallback=True)
    return stream.getvalue()


def restore_scheme_snapshot(scheme, snapshot: bytes) -> None:
    scheme.load_from(BytesIO(snapshot))


@dataclass(frozen=True)
class AiCommit:
    prompt: str
    backend: str
    model: str
    timestamp: datetime
    before_snapshot: bytes
    plan: CanvasPlan
    messages: list[str]

    @classmethod
    def create(
        cls,
        *,
        prompt: str,
        backend: str,
        model: str,
        before_snapshot: bytes,
        plan: CanvasPlan,
        messages: list[str],
    ) -> "AiCommit":
        return cls(
            prompt=prompt,
            backend=backend,
            model=model,
            timestamp=datetime.now(timezone.utc),
            before_snapshot=before_snapshot,
            plan=plan,
            messages=list(messages),
        )

    def revert(self, scheme) -> None:
        restore_scheme_snapshot(scheme, self.before_snapshot)

