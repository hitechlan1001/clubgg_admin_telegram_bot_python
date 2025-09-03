from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club
from src.utils.club_map import resolve_club_id
from src.library.send_credit import send_credit


async def _scr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 2)
        if not args:
            await update.message.reply_text("Usage: /scr <clubId> <amount>")
            return

        club_id_str = clean_id(args[0])
        amount_str = args[1].replace(",", "").strip()

        if not club_id_str.isdigit():
            await update.message.reply_text("❌ Invalid clubId.")
            return
        if not amount_str.isdigit():
            await update.message.reply_text("❌ Invalid amount.")
            return

        backend_id = resolve_club_id(club_id_str)
        club_id_num = int(backend_id)
        amount = int(amount_str)

        # Permission check
        check = can_manage_club(update, "scr", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Session cookie (set in bot startup / refresher)
        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        # Call API
        res = await send_credit(sid, backend_id, amount)
        if not res:
            await update.message.reply_text("❌ Failed to send credits (no response)")
            return
        if not res.get("ok"):
            msg = res.get("message")
            await update.message.reply_text(
                f"❌ Failed to send credits{f': {msg}' if msg else ''}"
            )
            return

        detail = res.get("message")
        msg = (
            "✅ *Credits Sent Successfully*\n\n"
            "🏛️ *Club Information*\n"
            f"🔑 Club ID : `{club_id_str}`\n"
            "💳 *Transaction*\n"
            f"• Amount: *{amount}*\n"
        )
        if detail:
            msg += f"\n📝 {detail}"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /scr:", e)
        await update.message.reply_text("❌ Unexpected error while sending credits.")


def register_scr(application) -> None:
    """
    Usage:
        from bot.commands.scr import register_scr
        register_scr(application)
    """
    application.add_handler(CommandHandler("scr", _scr))
