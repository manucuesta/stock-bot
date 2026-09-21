import asyncio
import os

from telegram import Bot

from .monitor import check_all


async def send_alerts(alerts: list[dict]) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    bot = Bot(token=token)

    for alert in alerts:

        source = alert["source"]
        result = alert["result"]

        price = result.get("price")

        if price is None:
            price_text = "Precio no detectado"
        else:
            price_text = f"{price:.2f} €"

        message = (
            "🚨 STOCK DETECTADO\n\n"
            f"🎮 {source['name']}\n"
            f"🏪 {source['store']}\n"
            f"💰 {price_text}\n"
            "🟢 Cumple tus condiciones\n\n"
            f"👉 {source['url']}"
        )

        await bot.send_message(
            chat_id=chat_id,
            text=message,
        )


def main() -> None:
    alerts = check_all()

    if alerts:
        asyncio.run(
            send_alerts(alerts)
        )


if __name__ == "__main__":
    main()