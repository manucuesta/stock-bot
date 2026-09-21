import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT_DIR / "data"
STATE_FILE = STATE_DIR / "state.json"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"states": {}}

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )


def get_source_state(state: dict, source_id: str) -> dict:
    states = state.setdefault("states", {})

    return states.setdefault(
        source_id,
        {
            "qualifies": False,
            "price": None,
        },
    )


def update_source_state(
    state: dict,
    source_id: str,
    qualifies: bool,
    price: float | None,
) -> None:
    source_state = get_source_state(state, source_id)

    source_state["qualifies"] = qualifies
    source_state["price"] = price