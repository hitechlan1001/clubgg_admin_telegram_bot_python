from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, CommandHandler


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "\n".join([
        "📖 *Command Guide*",
        "",
        "⚙️ *Limits* (Auto-detected from chat)",
        "• `/addwl <amt>`  — Increase Weekly *Win* Limit",
        "• `/subwl <amt>`  — Decrease Weekly *Win* Limit",
        "• `/addsl <amt>`  — Increase Weekly *Loss* Limit",
        "• `/subsl <amt>`  — Decrease Weekly *Loss* Limit",
        "• `/setwl <amt>`  — Set Weekly *Win* Limit to a value",
        "• `/setsl <amt>`  — Set Weekly *Loss* Limit to a value",
        "",
        "👁️ *View*",
        "• `/cl` — Show club limits *and* weekly P&L (Ring + Tournament)",
        "",
        "💳 *Credits* (Auto-detected from chat)",
        "• `/scr <amt>` — Send credits to club",
        "• `/ccr <amt>` — Claim credits from club",
        "",
        "—",
        "🧩 *Syntax & Examples*",
        "`/cl`",
        "`/addwl 5000`",
        "`/setsl 10000`",
        "`/scr 200`",
        "",
        "🛈 *Notes*",
        "• Club ID is automatically detected from the chat you're in.",
        "• Amounts are integers (no commas).",
        "• Access is role-based; some commands may be restricted.",
        "• Each club has its own dedicated chat group.",
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def register_help(application: Application) -> None:
    application.add_handler(CommandHandler("help", _help))
