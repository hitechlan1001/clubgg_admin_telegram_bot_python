from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club
from src.utils.club_map import resolve_club_id
from src.library.get_club_limit import get_club_limit
from src.library.set_limit import set_limit


async def _subsl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 2)
        if not args:
            await update.message.reply_text("Usage: /subsl <clubId> <amount>")
            return

        club_id_str = clean_id(args[0])
        amount_str = args[1].replace(",", "").strip()

        if not club_id_str.isdigit():
            await update.message.reply_text("❌ Invalid clubId.")
            return
        if not amount_str.lstrip("-").isdigit():
            await update.message.reply_text("❌ Invalid amount.")
            return

        backend_id = resolve_club_id(club_id_str)
        club_id_num = int(backend_id)
        amount = int(amount_str)

        # Role + scope
        check = can_manage_club(update, "subsl", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Fresh session from bot_data
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
        new_loss = prev_loss - amount

        # Update: keep win same, reduce loss
        res = await set_limit(sid, backend_id, prev_win, new_loss, 1)
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
            f"• 🔴 Weekly Loss Limit: *{new_loss}*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /subsl:", e)
        await update.message.reply_text("❌ Unexpected error while updating loss limit.")


def register_subsl(application) -> None:
    """
    Usage:
        from bot.commands.subsl import register_subsl
        register_subsl(application)
    """
    application.add_handler(CommandHandler("subsl", _subsl))
