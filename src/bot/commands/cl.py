from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.utils.parse import parse_args_safe, clean_id
from src.utils.can_manage_club import can_manage_club
from src.utils.club_map import resolve_club_id
from src.library.get_club_limit import get_club_limit
from src.library.get_club_pnl_for_club import get_club_pnl_for_club


async def _cl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text if update.message and update.message.text else ""
        args = parse_args_safe(text, 1)
        if not args:
            await update.message.reply_text("Usage: /cl <clubId>")
            return

        club_id_str = clean_id(args[0])
        if not club_id_str.isdigit():
            await update.message.reply_text("❌ Invalid clubId. Use a numeric ID, e.g. /cl 250793")
            return

        backend_id = resolve_club_id(club_id_str)
        club_id_num = int(backend_id)

        # Permission + scope check
        check = can_manage_club(update, "cl", club_id_num)
        if not check["allowed"]:
            await update.message.reply_text(f"❌ {check.get('reason', 'Not allowed')}")
            return

        # Fresh session (set during startup/refresh)
        sid = context.application.bot_data.get("sid")
        if not sid:
            await update.message.reply_text("❌ Session unavailable. Please try again.")
            return

        # Fetch current limits (clubId, sid)
        current = await get_club_limit(backend_id, sid)
        if not current or not current.INFO:
            await update.message.reply_text("❌ Failed to fetch current limits ")
            return

        info = current.INFO
        club_public_id = info.id
        club_name = info.nm
        win = info.win
        loss = info.loss

        # Fetch P&L from the list row for this club
        pnl = await get_club_pnl_for_club(backend_id, sid)
        ring = pnl.get("ringPnl", 0) if pnl else 0
        tour = pnl.get("tourneyPnl", 0) if pnl else 0
        weekly_earnings = ring + tour

        msg = (
            "🏛️ *Club Information*\n\n"
            f"🔑 *Club ID:* `{club_public_id}`\n"
            f"📛 *Club Name:* *{club_name}*\n\n"
            "⚙️ *Limits:*\n"
            f"• 🟢 Weekly Win Limit: *{win if win is not None else 'N/A'}*\n"
            f"• 🔴 Weekly Loss Limit: *{loss if loss is not None else 'N/A'}*\n\n"
            f"💰 *Weekly Club Earnings:* *{weekly_earnings}*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("Error in /cl:", e)
        await update.message.reply_text("❌ Unexpected error while fetching club limits.")


def register_cl(application) -> None:
    """
    Usage:
        from bot.commands.cl import register_cl
        register_cl(application)
    """
    application.add_handler(CommandHandler("cl", _cl))
