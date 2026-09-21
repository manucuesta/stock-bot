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


def parse_price(value: str) -> float | None:
    """
    Convierte precios europeos a float.

    Ejemplos:
        99,99       -> 99.99
        1.299,99    -> 1299.99
        99.99       -> 99.99
    """

    value = value.strip()
    value = value.replace("€", "").strip()

    if "," in value:
        value = value.replace(".", "")
        value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


def extract_product_price(
    soup: BeautifulSoup,
) -> float | None:
    """
    Intenta encontrar exclusivamente el precio principal
    del producto.

    Importante:
    No hacemos una búsqueda global de precios en toda la página,
    porque Amazon puede mostrar precios de productos relacionados,
    ofertas, recomendaciones, etc.
    """

    price_selectors = [
        "#corePriceDisplay_desktop_feature_div .a-price",
        "#corePriceDisplay_mobile_feature_div .a-price",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#priceblock_saleprice",
        ".priceToPay",
    ]

    for selector in price_selectors:

        element = soup.select_one(selector)

        if not element:
            continue

        # Amazon suele separar la parte entera y decimal.
        whole = element.select_one(".a-price-whole")
        fraction = element.select_one(".a-price-fraction")

        if whole:

            whole_text = whole.get_text(
                strip=True
            )

            fraction_text = (
                fraction.get_text(strip=True)
                if fraction
                else "00"
            )

            price = parse_price(
                f"{whole_text},{fraction_text}"
            )

            if price is not None:
                return price

        # Fallback para estructuras antiguas de Amazon.
        price_text = element.get_text(
            " ",
            strip=True,
        )

        match = re.search(
            r"(\d{1,4}(?:[.,]\d{2})?)\s*€",
            price_text,
        )

        if match:

            price = parse_price(
                match.group(1)
            )

            if price is not None:
                return price

    return None


def check(source: dict) -> dict:
    """
    Comprueba disponibilidad y precio de un producto Amazon.

    Estados posibles:

        available
            Producto disponible para comprar.

        not_qualified
            Producto correctamente identificado pero no
            disponible actualmente.

        unknown
            No hemos podido determinar el estado.
            Esto NO debe interpretarse como falta de stock.
    """

    # ------------------------------------------------------------------
    # Descargar página
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Texto general de la página
    # ------------------------------------------------------------------

    page_text = soup.get_text(
        " ",
        strip=True,
    ).lower()

    # ------------------------------------------------------------------
    # Detectar protección de Amazon
    # ------------------------------------------------------------------

    protection_terms = [
        "captcha",
        "introduce los caracteres",
        "robot",
        "sorry, we just need to make sure",
    ]

    for term in protection_terms:

        if term in page_text:

            return {
                "status": "unknown",
                "price": None,
                "reason": f"Amazon protection: {term}",
            }

    # ------------------------------------------------------------------
    # Comprobar disponibilidad
    # ------------------------------------------------------------------

    availability = soup.select_one(
        "#availability"
    )

    availability_text = ""

    if availability:

        availability_text = availability.get_text(
            " ",
            strip=True,
        ).lower()

    # Estas expresiones indican que NO podemos comprar ahora.
    unavailable_terms = [
        "no disponible por el momento",
        "no sabemos cuándo este producto volverá",
        "actualmente no disponible",
        "no disponible",
    ]

    for term in unavailable_terms:

        if term in availability_text:

            # MUY IMPORTANTE:
            #
            # Si Amazon dice que no está disponible,
            # NO buscamos ningún precio.
            #
            # Puede haber números en otras partes de la página
            # que no correspondan al precio actual del producto.

            return {
                "status": "not_qualified",
                "price": None,
                "reason": term,
            }

    # ------------------------------------------------------------------
    # Buscar elementos reales de compra
    # ------------------------------------------------------------------

    buy_selectors = [
        "#add-to-cart-button",
        "#buy-now-button",
        "input[name='submit.add-to-cart']",
        "input[name='submit.buy-now']",
    ]

    for selector in buy_selectors:

        element = soup.select_one(selector)

        if not element:
            continue

        # Solo buscamos el precio DESPUÉS de haber confirmado
        # que existe un elemento de compra.
        price = extract_product_price(
            soup
        )

        return {
            "status": "available",
            "price": price,
            "reason": f"Purchase element: {selector}",
        }

    # ------------------------------------------------------------------
    # No hemos podido determinar el estado
    # ------------------------------------------------------------------

    return {
        "status": "unknown",
        "price": None,
        "reason": "Amazon stock status not detected",
    }