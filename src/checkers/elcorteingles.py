from playwright.sync_api import sync_playwright


def check(source: dict) -> dict:
    """
    Abre la página de El Corte Inglés mediante Chromium
    y muestra información básica de lo que la web está mostrando.
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

            page.wait_for_timeout(3000)

            title = page.title()
            text = page.locator("body").inner_text()

            browser.close()

            print("\n========== EL CORTE INGLÉS ==========")
            print(f"Título: {title}")
            print("\nTexto encontrado:")
            print(text[:5000])
            print("========== FIN EL CORTE INGLÉS ==========\n")

            return {
                "status": "unknown",
                "price": None,
                "reason": "Diagnostic run",
            }

    except Exception as exc:

        return {
            "status": "unknown",
            "price": None,
            "reason": f"Playwright error: {exc}",
        }