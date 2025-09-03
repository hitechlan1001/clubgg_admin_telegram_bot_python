from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, CommandHandler


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "\n".join([
        "📖 *Command Guide*",
        "",
        "⚙️ *Limits*",
        "• `/addwl <id> <amt>`  — Increase Weekly *Win* Limit",
        "• `/subwl <id> <amt>`  — Decrease Weekly *Win* Limit",
        "• `/addsl <id> <amt>`  — Increase Weekly *Loss* Limit",
        "• `/subsl <id> <amt>`  — Decrease Weekly *Loss* Limit",
        "• `/setwl <id> <amt>`  — Set Weekly *Win* Limit to a value",
        "• `/setsl <id> <amt>`  — Set Weekly *Loss* Limit to a value",
        "",
        "👁️ *View*",
        "• `/cl <id>` — Show club limits *and* weekly P&L (Ring + Tournament)",
        "",
        "💳 *Credits*",
        "• `/scr <id> <amt>` — Send credits to club",
        "• `/ccr <id> <amt>` — Claim credits from club",
        "",
        "—",
        "🧩 *Syntax & Examples*",
        "`/cl 451214`",
        "`/addwl 451214 5000`",
        "`/setsl 451214 10000`",
        "`/scr 451214 200`",
        "",
        "🛈 *Notes*",
        "• Amounts are integers (no commas).",
        "• Access is role-based; some commands may be restricted.",
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def register_help(application: Application) -> None:
    application.add_handler(CommandHandler("help", _help))
