from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club

from src.library.claim_credit import claim_credit


async def _ccr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        
        # Parse command arguments
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 2)
        
        if not args:
            await update.message.reply_text("Usage: /ccr <club_id> <amount>\nExample: /ccr 492536 1000")
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
            if not amount_str.isdigit():
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
                    await update.message.reply_text(f"❌ {e}\n\n💡 You can also specify a club ID: /ccr <club_id> <amount>")
                else:
                    await update.message.reply_text(f"❌ {e}")
                return
            
            # Parse amount (first argument)
            amount_str = args[0].replace(",", "").strip()
            if not amount_str.isdigit():
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

        # Role + scope - Check permissions using display club ID, not backend ID
        check = can_manage_club(update, "ccr", int(club_id))
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Fresh SID from middleware (stored in bot_data by your startup)
        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        # (clubId, sid, amount)
        res = await claim_credit(str(backend_id), sid, amount)
        if not res:
            await update.message.reply_text("❌ Failed to claim credits (no response)")
            return
        if not res.get("ok"):
            msg = res.get("message")
            await update.message.reply_text(
                f"❌ Failed to claim credits{f': {msg}' if msg else ''}"
            )
            return

        detail = res.get("message")
        msg = (
            "✅ *Credits Claimed Successfully*\n\n"
            "🏛️ *Club Information*\n"
            f"🔑 Club ID : `{club_id}`\n"
            "💳 *Transaction*\n"
            f"• Amount: *{amount}*\n"
        )
        if detail:
            msg += f"\n📝 {detail}"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /ccr:", e)
        await update.message.reply_text("❌ Unexpected error while claiming credits.")


def register_ccr(application) -> None:
    """
    Usage:
        from bot.commands.ccr import register_ccr
        register_ccr(application)
    """
    application.add_handler(CommandHandler("ccr", _ccr))
