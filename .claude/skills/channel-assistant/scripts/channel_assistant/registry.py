"""Competitor channel registry backed by competitors.json."""

import json
from datetime import date
from pathlib import Path


class Registry:
    """Manages the competitor channel registry stored in a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> list[dict]:
        """Read and parse the competitors JSON file.

        Returns an empty list if the file does not exist yet.
        """
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data.get("channels", [])

    def save(self, channels: list[dict]) -> None:
        """Write channels to the JSON file with indentation."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"channels": channels}
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def add(
        self,
        name: str,
        youtube_id: str,
        url: str,
        notes: str = "",
    ) -> dict:
        """Add a new channel to the registry.

        Validates required fields, checks for duplicates, appends, saves,
        and returns the new entry.
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("Channel name is required and must be non-empty.")
        if not youtube_id or not youtube_id.strip():
            raise ValueError("youtube_id is required and must be non-empty.")
        if not youtube_id.startswith("@"):
            raise ValueError(
                f"youtube_id must start with '@' (handle format), got: {youtube_id!r}"
            )

        # Check for duplicates
        channels = self.load()
        for ch in channels:
            if ch.get("youtube_id") == youtube_id:
                raise ValueError(
                    f"A channel with youtube_id {youtube_id!r} already exists (duplicate)."
                )

        # Create and append new entry
        entry = {
            "name": name.strip(),
            "youtube_id": youtube_id.strip(),
            "url": url.strip() if url else "",
            "notes": notes.strip() if notes else "",
            "added": date.today().isoformat(),
        }
        channels.append(entry)
        self.save(channels)
        return entry

    def list_channels(self) -> list[dict]:
        """Return all channels in the registry."""
        return self.load()

    def get_by_name(self, name: str) -> dict | None:
        """Find a channel by name (case-insensitive partial match).

        Returns the first match, or None if not found.
        """
        query = name.lower()
        for ch in self.load():
            if query in ch.get("name", "").lower():
                return ch
        return None
