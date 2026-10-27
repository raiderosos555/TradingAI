from pathlib import Path
from .models import Blocked, read_json, utcnow


def read_observer(data_path, login, server, max_age=120, now=None):
    """Only inspect explicitly exported observer data within this terminal's MQL5/Files."""
    now = now or utcnow()
    root = (Path(data_path) / "MQL5" / "Files").resolve()
    results = []
    for path in (root / "TradingAI").glob("observer_*.json"):
        try:
            d = read_json(path)
            if d.get("schema_version") != "1.0" or d.get("read_only") is not True:
                raise Blocked("Unknown observer format")
            if d.get("account_login") != login or d.get("account_server") != server:
                continue
            if not -2 <= now.timestamp()-d["utc_time"] <= max_age:
                raise Blocked("Observer data stale")
            if d.get("screenshot"):
                image = (root / d["screenshot"]).resolve()
                if not image.is_relative_to(root) or image.suffix.lower() != ".png":
                    raise Blocked("Observer screenshot path escapes terminal file sandbox")
                d["screenshot"] = str(image) if image.is_file() else None
            results.append(d)
        except (Blocked, OSError, KeyError, TypeError) as exc:
            results.append({"file": path.name, "status": "UNAVAILABLE", "reason": str(exc)})
    return results
