from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club

from src.library.get_club_limit import get_club_limit
from src.library.set_limit import set_limit


async def _setwl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        
        # Parse command arguments
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 2)
        
        if not args:
            await update.message.reply_text("Usage: /setwl <club_id> <amount>\nExample: /setwl 492536 1000")
            return
        
        # Check if club ID is provided as first argument (only allowed in direct messages)
        if len(args) >= 2:
            # Only allow club ID parameter in direct messages (private chats)
            if update.effective_chat.type != "private":
                await update.message.reply_text("❌ Club ID parameter is only available in direct messages with the bot.")
                return
            
            try:
                club_id = int(args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid club ID. Please provide a valid number.")
                return
            
            # Parse amount (second argument)
            amount_str = args[1].replace(",", "").strip()
            if not amount_str.lstrip("-").isdigit():
                await update.message.reply_text("❌ Invalid amount.")
                return
            amount = int(amount_str)
        else:
            # Auto-detect club_id from chat context and use first argument as amount
            try:
                from src.bot.bot import get_chat_club_id
                club_id = get_chat_club_id(chat_id, context)
            except ValueError as e:
                if update.effective_chat.type == "private":
                    await update.message.reply_text(f"❌ {e}\n\n💡 You can also specify a club ID: /setwl <club_id> <amount>")
                else:
                    await update.message.reply_text(f"❌ {e}")
                return
            
            # Parse amount (first argument)
            amount_str = args[0].replace(",", "").strip()
            if not amount_str.lstrip("-").isdigit():
                await update.message.reply_text("❌ Invalid amount.")
                return
            amount = int(amount_str)
        
        # Map display club ID to backend ID
        try:
            from src.bot.bot import map_club_id
            backend_id = await map_club_id(club_id, context)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return

        # Role + scope check - Check permissions using display club ID, not backend ID
        check = can_manage_club(update, "setwl", int(club_id))
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Session from app state
        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        # Fetch current limits
        current = await get_club_limit(str(backend_id), sid)
        if not current or not current.INFO:
            await update.message.reply_text("❌ Failed to fetch current limits ")
            return

        info = current.INFO
        prev_win = int(info.win or 0)
        prev_loss = int(info.loss or 0)

        # Update: set win to amount, keep loss the same
        res = await set_limit(sid, str(backend_id), amount, prev_loss, 1)
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
            f"• 🟢 Weekly Win Limit: *{amount}*\n"
            f"• 🔴 Weekly Loss Limit: *{prev_loss}*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /setwl:", e)
        await update.message.reply_text("❌ Unexpected error while updating win limit.")


def register_setwl(application) -> None:
    """
    Usage:
        from bot.commands.setwl import register_setwl
        register_setwl(application)
    """
    application.add_handler(CommandHandler("setwl", _setwl))
