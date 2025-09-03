from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club
from src.utils.club_map import resolve_club_id
from src.library.get_club_limit import get_club_limit
from src.library.set_limit import set_limit


async def _setsl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 2)
        if not args:
            await update.message.reply_text("Usage: /setsl <clubId> <amount>")
            return

        club_id_str = clean_id(args[0])
        amount_str = args[1].replace(",", "")

        if not club_id_str.isdigit():
            await update.message.reply_text("❌ Invalid clubId.")
            return
        # allow negative with leading '-' only
        if not (amount_str.lstrip("-").isdigit()):
            await update.message.reply_text("❌ Invalid amount.")
            return

        backend_id = resolve_club_id(club_id_str)
        club_id_num = int(backend_id)
        amount = int(amount_str)

        # Role + scope
        check = can_manage_club(update, "setsl", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason','Not allowed')}")
            return

        # Fresh session from middleware (stored in bot_data)
        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        # Fetch current limits
        current = await get_club_limit(backend_id, sid)
        if not current or not current.INFO:
            await update.message.reply_text("❌ Failed to fetch current limits ")
            return

        info = current.INFO
        prev_win = int(info.win or 0)
        prev_loss = int(info.loss or 0)

        # Update: keep win same, set loss to amount
        res = await set_limit(sid, backend_id, prev_win, amount, 1)
        if not res:
            await update.message.reply_text("❌ Failed to update limits.")
            return

        msg = (
            "✅ *Weekly Loss Limit Updated Successfully*\n\n"
            "🏛️ *Club Information*\n"
            f"🔑 Club ID: `{club_id_str}`\n"
            f"📛 Club Name: *{info.nm}*\n\n"
            "📊 *Previous Limits:*\n"
            f"• 🟢 Weekly Win Limit: *{prev_win}*\n"
            f"• 🔴 Weekly Loss Limit: *{prev_loss}*\n\n"
            "📊 *Updated Limits:*\n"
            f"• 🟢 Weekly Win Limit: *{prev_win}*\n"
            f"• 🔴 Weekly Loss Limit: *{amount}*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /setsl:", e)
        await update.message.reply_text("❌ Unexpected error while updating loss limit.")


def register_setsl(application) -> None:
    """
    Usage:
        from bot.commands.setsl import register_setsl
        register_setsl(application)
    """
    application.add_handler(CommandHandler("setsl", _setsl))
