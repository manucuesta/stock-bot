from .amazon import check as amazon_check
from .carrefour import check as carrefour_check
from .elcorteingles import check as elcorteingles_check
from .game import check as game_check
from .generic import check as generic_check
from .mediamarkt import check as mediamarkt_check
from .pccomponentes import check as pccomponentes_check


CHECKERS = {
    "amazon": amazon_check,
    "carrefour": carrefour_check,
    "elcorteingles": elcorteingles_check,
    "game": game_check,
    "mediamarkt": mediamarkt_check,
    "pccomponentes": pccomponentes_check,
    "generic": generic_check,
}


def check_source(source: dict) -> dict:
    checker_type = source.get("type", "generic")

    checker = CHECKERS.get(
        checker_type,
        generic_check,
    )

    return checker(source)