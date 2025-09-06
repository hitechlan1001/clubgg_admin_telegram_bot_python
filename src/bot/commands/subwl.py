from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club

from src.library.get_club_limit import get_club_limit
from src.library.set_limit import set_limit


async def _subwl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            await update.message.reply_text("Usage: /subwl <amount>")
            return

        amount_str = args[0].replace(",", "").strip()
        if not amount_str.lstrip("-").isdigit():
            await update.message.reply_text("❌ Invalid amount.")
            return

        club_id_num = int(backend_id)
        amount = int(amount_str)

        # Role + scope check
        check = can_manage_club(update, "subwl", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Fresh session from app state
        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        # Fetch current limits
        current = await get_club_limit(str(backend_id), sid)
        if not current or not current.INFO:
            await update.message.reply_text("❌ Failed to fetch current limits")
            return

        info = current.INFO
        prev_win = int(info.win or 0)
        prev_loss = int(info.loss or 0)
        
        # Fix: Handle negative values correctly for subwl (decrease win limit)
        if prev_win < 0:
            # When negative, "sub" means make it LESS negative (add)
            new_win = prev_win + amount
        else:
            # When positive, "sub" means subtract from the value
            new_win = prev_win - amount

        # Update win limit, keep loss the same
        res = await set_limit(sid, str(backend_id), new_win, prev_loss, 1)
        if not res:
            await update.message.reply_text("❌ Failed to update limits.")
            return

        msg = (
            "✅ *Weekly Win Limit Updated Successfully*\n\n"
            "🏛️ *Club Information*\n"
            f"🔑 Club ID: `{club_id}`\n"
            f"📛 Club Name: *{info.nm}*\n\n"
            "📊 *Previous Limits:*\n"
            f"• 🟢 Weekly Win Limit: *{prev_win}*\n"
            f"• 🔴 Weekly Loss Limit: *{prev_loss}*\n\n"
            "📊 *Updated Limits:*\n"
            f"• 🟢 Weekly Win Limit: *{new_win}*\n"
            f"• 🔴 Weekly Loss Limit: *{prev_loss}*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /subwl:", e)
        await update.message.reply_text("❌ Unexpected error while updating win limit.")


def register_subwl(application) -> None:
    """
    Usage:
        from bot.commands.subwl import register_subwl
        register_subwl(application)
    """
    application.add_handler(CommandHandler("subwl", _subwl))
