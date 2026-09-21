import os
import uuid

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .config import load_sources, save_sources


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# Estados de la conversación /add
ADD_URL, ADD_NAME, ADD_STORE, ADD_PRICE = range(4)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def is_authorized(update: Update) -> bool:
    if update.effective_chat is None:
        return False

    return str(update.effective_chat.id) == TELEGRAM_CHAT_ID


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ Cancelar",
                callback_data="add:cancel",
            )
        ]
    ])


# ---------------------------------------------------------------------------
# Comandos básicos
# ---------------------------------------------------------------------------

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not is_authorized(update):
        return

    await update.message.reply_text(
        "🤖 Stock Hunter activo.\n\n"
        "Puedo vigilar productos y avisarte cuando "
        "aparezcan disponibles al precio que quieras.\n\n"
        "Comandos:\n"
        "/add — añadir seguimiento\n"
        "/list — ver seguimientos\n"
        "/help — ayuda"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not is_authorized(update):
        return

    await update.message.reply_text(
        "📖 AYUDA\n\n"
        "/add — añadir un producto\n"
        "/list — ver productos seguidos\n"
        "/cancel — cancelar una operación\n\n"
        "El bot comprobará automáticamente las tiendas "
        "y te avisará cuando un producto cumpla tus condiciones."
    )


# ---------------------------------------------------------------------------
# /add
# ---------------------------------------------------------------------------

async def add_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    if not is_authorized(update):
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "🔗 **Añadir seguimiento**\n\n"
        "Envíame la URL exacta del producto que quieres seguir.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )

    return ADD_URL


async def add_url(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text(
            "❌ Eso no parece una URL válida.\n\n"
            "Envíame una URL que empiece por http:// o https://",
            reply_markup=cancel_keyboard(),
        )

        return ADD_URL

    context.user_data["url"] = url

    await update.message.reply_text(
        "📝 Perfecto.\n\n"
        "¿Qué nombre quieres ponerle al producto?",
        reply_markup=cancel_keyboard(),
    )

    return ADD_NAME


async def add_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ El nombre no puede estar vacío."
        )
        return ADD_NAME

    context.user_data["name"] = name

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 Amazon",
                callback_data="store:amazon",
            ),
            InlineKeyboardButton(
                "🛒 Carrefour",
                callback_data="store:carrefour",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎮 GAME",
                callback_data="store:game",
            ),
            InlineKeyboardButton(
                "📺 MediaMarkt",
                callback_data="store:mediamarkt",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏪 Otra tienda",
                callback_data="store:generic",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancelar",
                callback_data="add:cancel",
            )
        ],
    ]

    await update.message.reply_text(
        "🏪 ¿Qué tienda es?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_STORE


async def add_store(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    query = update.callback_query

    await query.answer()

    if not is_authorized(update):
        return ConversationHandler.END

    store_type = query.data.split(":", 1)[1]

    store_names = {
        "amazon": "Amazon",
        "carrefour": "Carrefour",
        "game": "GAME",
        "mediamarkt": "MediaMarkt",
        "generic": "Otra tienda",
    }

    context.user_data["type"] = store_type
    context.user_data["store"] = store_names[store_type]

    keyboard = [
        [
            InlineKeyboardButton(
                "♾️ Sin límite",
                callback_data="price:none",
            )
        ],
        [
            InlineKeyboardButton(
                "50 €",
                callback_data="price:50",
            ),
            InlineKeyboardButton(
                "100 €",
                callback_data="price:100",
            ),
        ],
        [
            InlineKeyboardButton(
                "150 €",
                callback_data="price:150",
            ),
        ],
        [
            InlineKeyboardButton(
                "✏️ Otro",
                callback_data="price:custom",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancelar",
                callback_data="add:cancel",
            )
        ],
    ]

    await query.edit_message_text(
        "💰 ¿Cuál es el precio máximo que estás dispuesto a pagar?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_PRICE


async def add_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    query = update.callback_query

    await query.answer()

    if not is_authorized(update):
        return ConversationHandler.END

    value = query.data.split(":", 1)[1]

    if value == "none":
        context.user_data["price_max"] = None

    elif value == "custom":
        await query.edit_message_text(
            "✏️ Escribe el precio máximo.\n\n"
            "Ejemplo: `89.99`",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard(),
        )

        context.user_data["waiting_custom_price"] = True

        return ADD_PRICE

    else:
        context.user_data["price_max"] = float(value)

    return await finish_add(update, context)


async def add_custom_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    value = update.message.text.strip().replace(",", ".")

    try:
        price = float(value)

        if price <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ No parece un precio válido.\n\n"
            "Escribe algo como `89.99`.",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard(),
        )

        return ADD_PRICE

    context.user_data["price_max"] = price

    return await finish_add(update, context)


async def finish_add(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    sources = load_sources()

    source = {
        "id": str(uuid.uuid4()),
        "name": context.user_data["name"],
        "store": context.user_data["store"],
        "url": context.user_data["url"],
        "type": context.user_data["type"],
        "price_max": context.user_data["price_max"],
        "enabled": True,
    }

    sources.append(source)
    save_sources(sources)

    price_max = source["price_max"]

    if price_max is None:
        price_text = "Sin límite"
    else:
        price_text = f"{price_max:.2f} €"

    text = (
        "✅ **Seguimiento creado**\n\n"
        f"🎮 {source['name']}\n"
        f"🏪 {source['store']}\n"
        f"💰 Precio máximo: {price_text}\n\n"
        f"🔗 {source['url']}"
    )

    # Si venimos de un botón, editamos el mensaje.
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
        )

    context.user_data.clear()

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# /cancel
# ---------------------------------------------------------------------------

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.answer()

        await update.callback_query.edit_message_text(
            "❌ Operación cancelada."
        )
    else:
        await update.message.reply_text(
            "❌ Operación cancelada."
        )

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# /list
# ---------------------------------------------------------------------------

async def list_sources(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not is_authorized(update):
        return

    sources = load_sources()

    if not sources:
        await update.message.reply_text(
            "📭 No estás siguiendo ningún producto.\n\n"
            "Usa /add para añadir uno."
        )
        return

    for index, source in enumerate(sources, start=1):

        price_max = source.get("price_max")

        if price_max is None:
            price_text = "♾️ Sin límite"
        else:
            price_text = f"💰 ≤ {price_max:.2f} €"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🗑️ Eliminar",
                    callback_data=f"remove:{source['id']}",
                )
            ]
        ]

        await update.message.reply_text(
            f"**{index}. {source['name']}**\n\n"
            f"🏪 {source['store']}\n"
            f"{price_text}\n\n"
            f"🔗 {source['url']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ---------------------------------------------------------------------------
# Eliminar
# ---------------------------------------------------------------------------

async def remove_source(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    await query.answer()

    if not is_authorized(update):
        return

    source_id = query.data.split(":", 1)[1]

    sources = load_sources()

    source = next(
        (
            source
            for source in sources
            if source["id"] == source_id
        ),
        None,
    )

    if source is None:
        await query.edit_message_text(
            "⚠️ Este seguimiento ya no existe."
        )
        return

    sources = [
        source
        for source in sources
        if source["id"] != source_id
    ]

    save_sources(sources)

    await query.edit_message_text(
        "🗑️ **Seguimiento eliminado**\n\n"
        f"🎮 {source['name']}\n"
        f"🏪 {source['store']}",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:

    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN no está configurado."
        )

    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    add_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_start),
        ],
        per_message=False,
        states={
            ADD_URL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_url,
                ),
                CallbackQueryHandler(
                    cancel,
                    pattern=r"^add:cancel$",
                ),
            ],

            ADD_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_name,
                ),
                CallbackQueryHandler(
                    cancel,
                    pattern=r"^add:cancel$",
                ),
            ],

            ADD_STORE: [
                CallbackQueryHandler(
                    add_store,
                    pattern=r"^store:",
                ),
                CallbackQueryHandler(
                    cancel,
                    pattern=r"^add:cancel$",
                ),
            ],

            ADD_PRICE: [
                CallbackQueryHandler(
                    add_price,
                    pattern=r"^price:",
                ),
                CallbackQueryHandler(
                    cancel,
                    pattern=r"^add:cancel$",
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_custom_price,
                ),
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(
                cancel,
                pattern=r"^add:cancel$",
            ),
        ],
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("list", list_sources)
    )

    application.add_handler(
        CallbackQueryHandler(
            remove_source,
            pattern=r"^remove:",
        )
    )

    application.add_handler(add_conversation)

    print("🤖 Stock Hunter iniciado...")
    print("Pulsa Ctrl+C para detenerlo.")

    application.run_polling()


if __name__ == "__main__":
    main()