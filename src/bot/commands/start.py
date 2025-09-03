from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, CommandHandler


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    c = update.effective_chat
    text = (
        f"👋 Welcome, *{u.first_name}*!\n\n"
        f"📌 *Your Details:*\n"
        f"• 🆔 Telegram ID: `{u.id}`\n"
        f"• 💬 Chat ID: `{c.id}`\n\n"
        f"⚡ Use /help anytime to see the list of available commands."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def register_start(application: Application) -> None:
    application.add_handler(CommandHandler("start", _start))
