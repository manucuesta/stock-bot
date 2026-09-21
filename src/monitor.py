from .checkers import check_source
from .config import load_sources
from .state import (
    get_source_state,
    load_state,
    save_state,
    update_source_state,
)


def qualifies(
    source: dict,
    result: dict,
) -> bool:
    """
    Determina si un producto cumple las condiciones
    configuradas por el usuario.
    """

    if result["status"] != "available":
        return False

    price = result.get("price")
    price_max = source.get("price_max")

    if price_max is not None:

        # Si hemos detectado stock pero no precio,
        # no podemos afirmar que cumple el límite.
        if price is None:
            return False

        if price > price_max:
            return False

    return True


def check_all() -> list[dict]:
    sources = load_sources()
    state = load_state()

    alerts = []

    for source in sources:

        result = check_source(source)

        previous = get_source_state(
            state,
            source["id"],
        )

        previous_qualifies = previous.get(
            "qualifies",
            False,
        )

        # Un error de scraping NO modifica el estado.
        if result["status"] == "unknown":
            print(
                f"⚪ {source['store']} - "
                f"{source['name']} - "
                f"UNKNOWN: {result['reason']}"
            )

            continue

        current_qualifies = qualifies(
            source,
            result,
        )

        print(
            f"{'🟢' if current_qualifies else '🔴'} "
            f"{source['store']} - "
            f"{source['name']} - "
            f"price={result.get('price')} - "
            f"{result['reason']}"
        )

        # Solo alertamos cuando entra en estado válido.
        if current_qualifies and not previous_qualifies:
            alerts.append({
                "source": source,
                "result": result,
            })

        update_source_state(
            state,
            source["id"],
            current_qualifies,
            result.get("price"),
        )

    save_state(state)

    return alerts