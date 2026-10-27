"""Transport boundary: future connectors implement this protocol, without execution privileges."""
from pathlib import Path
from typing import Protocol

from .journal import atomic_write
from .models import canonical, read_json, validate_briefing


class BriefingTransport(Protocol):
    def incoming(self) -> list[Path]: ...
    def read(self, path: Path) -> dict: ...
    def publish(self, report: dict, markdown: str) -> None: ...


class FileTransport:
    def __init__(self, root):
        self.root = Path(root)
        for d in ("inbox", "outbox"):
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def incoming(self):
        return sorted((self.root / "inbox").glob("*.json"))

    def read(self, path):
        return validate_briefing(read_json(path))

    def publish(self, report, markdown):
        name = report["report_id"]
        atomic_write(self.root / "outbox" / f"{name}.json", canonical(report) + "\n")
        atomic_write(self.root / "outbox" / f"{name}.md", markdown)
        # Consumers watch this manifest; it is updated only after both immutable files exist.
        atomic_write(self.root / "outbox" / "latest.json", canonical({"schema_version": "1.0", "report_id": name,
                     "json": f"{name}.json", "markdown": f"{name}.md"}) + "\n")
