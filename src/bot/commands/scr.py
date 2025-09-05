from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club

from src.library.send_credit import send_credit


async def _scr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        
        chat_id = update.effective_chat.id
        
        # Auto-detect club_id from chat context using PM's method
        try:
            from src.bot.bot import get_chat_club_id, map_club_id
            club_id = get_chat_club_id(chat_id, context)
            backend_id = await map_club_id(club_id, context)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return
        
        # Parse amount from command
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 1)
        if not args:
            await update.message.reply_text("Usage: /scr <amount>")
            return

        amount_str = args[0].replace(",", "").strip()
        if not amount_str.isdigit():
            await update.message.reply_text("❌ Invalid amount.")
            return

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
        res = await send_credit(sid, str(backend_id), amount)
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
            f"🔑 Club ID : `{club_id}`\n"
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
