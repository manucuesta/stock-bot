import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
SOURCES_FILE = CONFIG_DIR / "sources.json"


def load_sources() -> list[dict]:
    if not SOURCES_FILE.exists():
        return []

    with SOURCES_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("sources", [])


def save_sources(sources: list[dict]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with SOURCES_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            {"sources": sources},
            file,
            indent=2,
            ensure_ascii=False,
        )


def add_source(source: dict) -> None:
    sources = load_sources()
    sources.append(source)
    save_sources(sources)


def remove_source(source_id: str) -> dict | None:
    sources = load_sources()

    removed = None
    remaining = []

    for source in sources:
        if source["id"] == source_id:
            removed = source
        else:
            remaining.append(source)

    if removed is not None:
        save_sources(remaining)

    return removed