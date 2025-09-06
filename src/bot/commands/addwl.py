from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club
from src.library.get_club_limit import get_club_limit
from src.library.set_limit import set_limit


async def _addwl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
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
            await update.message.reply_text("Usage: /addwl <amount>")
            return

        amount_str = args[0].replace(",", "").strip()
        if not (amount_str.lstrip("-").isdigit()):
            await update.message.reply_text("❌ Invalid amount.")
            return

        club_id_num = int(backend_id)
        amount = int(amount_str)

        # Role + scope
        check = can_manage_club(update, "addwl", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Fresh session from bot_data (populated by your SID refresher)
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
        
        # Fix: Handle negative values correctly for addwl (increase win limit)
        if prev_win < 0:
            # When negative, "add" means make it MORE negative (subtract)
            new_win = prev_win - amount
        else:
            # When positive, "add" means add to the value
            new_win = prev_win + amount

        # Update limits (win changes, loss stays)
        res = await set_limit(sid, str(backend_id), new_win, prev_loss, 1)
        if not res:
            await update.message.reply_text("❌ Failed to update limits (no response from server)")
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
        print("Error in /addwl:", e)
        await update.message.reply_text("❌ Unexpected error while updating win limit.")


def register_addwl(application) -> None:
    """
    Usage in your bot startup:
        from bot.commands.addwl import register_addwl
        register_addwl(application)
    """
    application.add_handler(CommandHandler("addwl", _addwl))
