import re

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


OUT_OF_STOCK_TERMS = [
    "agotado",
    "sin stock",
    "no disponible",
    "fuera de stock",
    "próximamente",
    "proximamente",
    "avísame",
    "avisame",
    "notificarme",
]


IN_STOCK_TERMS = [
    "añadir al carrito",
    "añadir a la cesta",
    "comprar ahora",
    "comprar",
    "en stock",
    "disponible",
]


def extract_price(text: str) -> float | None:
    patterns = [
        r"(\d{1,4}(?:[.,]\d{2})?)\s*€",
        r"€\s*(\d{1,4}(?:[.,]\d{2})?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if not match:
            continue

        value = match.group(1)

        # 1.234,56 -> 1234.56
        if "," in value and "." in value:
            value = value.replace(".", "").replace(",", ".")

        # 99,99 -> 99.99
        elif "," in value:
            value = value.replace(",", ".")

        try:
            return float(value)
        except ValueError:
            continue

    return None


def check(source: dict) -> dict:
    try:
        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        return {
            "status": "unknown",
            "price": None,
            "reason": f"HTTP error: {exc}",
        }

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Elimina scripts/styles para que el texto sea más útil.
    for element in soup([
        "script",
        "style",
        "noscript",
    ]):
        element.decompose()

    text = soup.get_text(
        " ",
        strip=True,
    ).lower()

    price = extract_price(text)

    # Primero comprobamos señales inequívocas de falta de stock.
    for term in OUT_OF_STOCK_TERMS:
        if term in text:
            return {
                "status": "not_qualified",
                "price": price,
                "reason": f"Out-of-stock term: {term}",
            }

    # Después buscamos señales de compra.
    for term in IN_STOCK_TERMS:
        if term in text:
            return {
                "status": "available",
                "price": price,
                "reason": f"In-stock term: {term}",
            }

    # La página ha respondido, pero no sabemos interpretar su estado.
    return {
        "status": "unknown",
        "price": price,
        "reason": "No stock signal detected",
    }