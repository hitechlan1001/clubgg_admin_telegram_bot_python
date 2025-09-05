from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club
from src.library.get_club_limit import get_club_limit
from src.library.get_club_pnl_for_club import get_club_pnl_for_club

async def _cl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        
        try:
            from src.bot.bot import get_chat_club_id, map_club_id
            club_id = get_chat_club_id(chat_id, context)
            backend_id = await map_club_id(club_id, context)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return
        
        club_id_num = int(backend_id)

        check = can_manage_club(update, "cl", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        current = await get_club_limit(str(backend_id), sid)
        if not current or not current.INFO:
            await update.message.reply_text("❌ Failed to fetch current limits ")
            return
        
        info = current.INFO
        club_public_id = info.id
        club_name = info.nm
        win_limit = int(info.win or 0)
        loss_limit = int(info.loss or 0)
        pnl_data = await get_club_pnl_for_club(str(backend_id), sid)
        ring_pnl = int(pnl_data.ring_pnl or 0) if pnl_data else 0
        tournament_pnl = int(pnl_data.tournament_pnl or 0) if pnl_data else 0
        total_pnl = ring_pnl + tournament_pnl

        msg = (
            f"🏛️ Club Information\n\n"
            f"🔑 Club ID: {club_id}\n"
            f"📛 Club Name: {club_name}\n\n"
            f"⚙️ Limits:\n"
            f"• 🟢 Weekly Win Limit: {win_limit:,}\n"
            f"• 🔴 Weekly Loss Limit: {loss_limit:,}\n\n"
            f"💰 Weekly Club Earnings: {total_pnl:,}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /cl:", e)
        await update.message.reply_text("❌ Unexpected error while fetching club limits.")

def register_cl(application) -> None:
    application.add_handler(CommandHandler("cl", _cl))