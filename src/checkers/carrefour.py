import re

from playwright.sync_api import sync_playwright


UNAVAILABLE_TERMS = [
    "agotado temporalmente",
    "agotado",
    "sin stock",
    "no disponible",
    "producto no disponible",
]

AVAILABLE_TERMS = [
    "añadir al carrito",
    "añadir a la cesta",
    "comprar",
]


def parse_price(text: str) -> float | None:
    """
    Convierte precios españoles como:

    99,99 €
    1.299,99 €
    99.99 €

    en float.
    """
    if not text:
        return None

    match = re.search(
        r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:[.,]\d{2}))\s*€",
        text,
    )

    if not match:
        return None

    value = match.group(1)

    if "." in value and "," in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


def check(source: dict) -> dict:
    """
    Comprueba un producto de Carrefour mediante Chromium/Playwright.
    """

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True
            )

            page = browser.new_page(
                locale="es-ES",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/153.0.0.0 Safari/537.36"
                ),
                viewport={
                    "width": 1920,
                    "height": 1080,
                },
            )

            page.goto(
                source["url"],
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Esperamos a que Carrefour termine de cargar
            # contenido dinámico.
            page.wait_for_timeout(5000)

            title = page.title()

            text = page.locator("body").inner_text()

            text_lower = text.lower()

            # --------------------------------------------------
            # DIAGNÓSTICO TEMPORAL
            # --------------------------------------------------

            print("\n========== CARREFOUR DIAGNOSTIC ==========")
            print(f"Título: {title}")
            print(f"URL final: {page.url}")
            print(f"Longitud texto: {len(text)}")
            print("\nPrimeros 5000 caracteres:")
            print(text[:5000])
            print("\n===========================================\n")

            # --------------------------------------------------
            # 1. Comprobar si Carrefour está bloqueando el acceso
            # --------------------------------------------------

            protection_terms = [
                "access denied",
                "access forbidden",
                "captcha",
                "verify you are human",
                "robot check",
                "just a moment",
            ]

            for term in protection_terms:
                if term in text_lower:
                    browser.close()

                    return {
                        "status": "unknown",
                        "price": None,
                        "reason": f"Possible protection page: {term}",
                    }

            # --------------------------------------------------
            # 2. Comprobar disponibilidad
            # --------------------------------------------------

            for term in UNAVAILABLE_TERMS:
                if term in text_lower:
                    browser.close()

                    return {
                        "status": "not_qualified",
                        "price": None,
                        "reason": f"Unavailable: {term}",
                    }

            # --------------------------------------------------
            # 3. Buscar señales de disponibilidad
            # --------------------------------------------------

            available = False

            for term in AVAILABLE_TERMS:
                if term in text_lower:
                    available = True
                    break

            # También comprobamos botones reales.
            if not available:
                buttons = page.locator("button").all_inner_texts()

                for button_text in buttons:
                    button_lower = button_text.lower()

                    if any(
                        term in button_lower
                        for term in AVAILABLE_TERMS
                    ):
                        available = True
                        break

            if not available:
                browser.close()

                return {
                    "status": "unknown",
                    "price": None,
                    "reason": "Could not determine availability",
                }

            # --------------------------------------------------
            # 4. Producto disponible -> buscar precio
            # --------------------------------------------------

            price = None

            price_selectors = [
                '[class*="price"]',
                '[data-testid*="price"]',
                '[data-test*="price"]',
            ]

            for selector in price_selectors:
                elements = page.locator(selector)

                count = min(elements.count(), 20)

                for index in range(count):
                    try:
                        element_text = elements.nth(index).inner_text()

                        parsed = parse_price(element_text)

                        if parsed is not None:
                            price = parsed
                            break

                    except Exception:
                        continue

                if price is not None:
                    break

            # Como fallback, buscamos un precio en el texto
            # cercano a la parte superior de la página.
            if price is None:
                price = parse_price(text[:5000])

            browser.close()

            if price is None:
                return {
                    "status": "unknown",
                    "price": None,
                    "reason": (
                        "Product appears available "
                        "but price could not be detected"
                    ),
                }

            return {
                "status": "available",
                "price": price,
                "reason": f"Available - {price:.2f} €",
            }

    except Exception as exc:
        return {
            "status": "unknown",
            "price": None,
            "reason": f"Playwright error: {exc}",
        }