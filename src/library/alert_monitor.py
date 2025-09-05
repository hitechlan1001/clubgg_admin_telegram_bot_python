import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from telegram import Bot
from telegram.error import TelegramError

from .get_all_club_limits import get_all_club_limits
from ..utils.roles import user_roles

logger = logging.getLogger(__name__)

LOSS_LIMIT_WARNING_PERCENT = 90.0
WIN_LIMIT_WARNING_PERCENT = 90.0
PNL_NEGATIVE_THRESHOLD = -1000.0
CHECK_INTERVAL_MINUTES = 1
ALERT_COOLDOWN_MINUTES = 5

last_alert_times: Dict[str, datetime] = {}
alert_cooldown = timedelta(minutes=ALERT_COOLDOWN_MINUTES)

def parse_numeric_value(value_str: str) -> float:
    if not value_str or value_str.strip() == "":
        return 0.0
    try:
        return float(str(value_str).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0

def should_send_alert(club_id: int, alert_type: str) -> bool:
    key = f"{club_id}_{alert_type}"
    last_alert = last_alert_times.get(key)
    if not last_alert:
        return True
    return datetime.now() - last_alert > alert_cooldown

def update_alert_time(club_id: int, alert_type: str):
    key = f"{club_id}_{alert_type}"
    last_alert_times[key] = datetime.now()

def get_alert_recipients(club_id: int, application) -> List[int]:
    chat_club_map = application.bot_data.get("chat_club_map", {})
    for chat_id, mapped_club_id in chat_club_map.items():
        if mapped_club_id == club_id:
            return [chat_id]
    
    recipients = []
    for user_id, roles in user_roles.items():
        if "admin" in roles or "manager" in roles:
            recipients.append(user_id)
    
    return recipients

async def send_alert(bot: Bot, message: str, chat_id: int, club_id: int):
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        update_alert_time(club_id, "general")
        logger.info(f"Alert sent to chat {chat_id} for club {club_id}")
    except TelegramError as e:
        logger.error(f"Failed to send alert to chat {chat_id}: {e}")

async def check_club_limits(bot: Bot, application):
    try:
        sid = application.bot_data.get("sid")
        if not sid:
            logger.warning("No SID available for limit checking")
            return

        club_data = await get_all_club_limits(sid)
        if not club_data or not club_data.DATA:
            logger.warning("No club data available")
            return

        total_alerts_sent = 0

        for club in club_data.DATA:
            try:
                club_id = int(club.cno)
                win_limit = parse_numeric_value(club.f7)  # f7 is win limit
                loss_limit = parse_numeric_value(club.f6)  # f6 is loss limit
                win_usage = 0  # Usage not available in this API
                loss_usage = 0  # Usage not available in this API

                if win_limit <= 0 and loss_limit <= 0:
                    continue

                if loss_limit > 0:
                    loss_percentage = (loss_usage / loss_limit) * 100
                    if loss_percentage >= LOSS_LIMIT_WARNING_PERCENT and should_send_alert(club_id, "loss"):
                        message = f"🚨 *Loss Limit Alert*\n\n" \
                                f"🏛️ *Club:* {club.f2}\n" \
                                f"📊 *Loss Limit:* ${loss_limit:,.2f}\n" \
                                f"📈 *Usage:* {loss_percentage:.1f}%"
                       
                        recipients = get_alert_recipients(club_id, application)
                        for chat_id in recipients:
                            await send_alert(bot, message, chat_id, club_id)
                            total_alerts_sent += 1

                if win_limit > 0:
                    win_percentage = (win_usage / win_limit) * 100
                    if win_percentage >= WIN_LIMIT_WARNING_PERCENT and should_send_alert(club_id, "win"):
                        message = f"🚨 *Win Limit Alert*\n\n" \
                                f"🏛️ *Club:* {club.f2}\n" \
                                f"📊 *Win Limit:* ${win_limit:,.2f}\n" \
                                f"📈 *Usage:* {win_percentage:.1f}%"
                       
                        recipients = get_alert_recipients(club_id, application)
                        for chat_id in recipients:
                            await send_alert(bot, message, chat_id, club_id)
                            total_alerts_sent += 1

                ring_pnl = parse_numeric_value(club.f4)  # f4 is ring P&L
                tournament_pnl = parse_numeric_value(club.f5)  # f5 is tournament P&L
                total_pnl = ring_pnl + tournament_pnl

                if total_pnl <= PNL_NEGATIVE_THRESHOLD and should_send_alert(club_id, "pnl"):
                    message = f"🚨 *P&L Alert*\n\n" \
                            f"🏛️ *Club:* {club.f2}\n" \
                            f"💰 *Total P&L:* ${total_pnl:,.2f}\n" \
                            f"🎰 *Ring Game P&L:* ${ring_pnl:,.2f}\n" \
                            f"🏆 *Tournament P&L:* ${tournament_pnl:,.2f}"
                   
                    recipients = get_alert_recipients(club_id, application)
                    for chat_id in recipients:
                        await send_alert(bot, message, chat_id, club_id)
                        total_alerts_sent += 1

            except Exception as e:
                logger.error(f"Error processing club {club.cno}: {e}")
                continue

        if total_alerts_sent > 0:
            logger.info(f"Sent {total_alerts_sent} alerts")

    except Exception as e:
        logger.error(f"Error in limit checking: {e}")

async def start_alert_monitoring(bot, application):
    logger.info("Alert monitoring started")
    
    while True:
        try:
            await check_club_limits(bot, application)
        except Exception as e:
            logger.error(f"Alert monitoring error: {e}")
        
        await asyncio.sleep(60 * CHECK_INTERVAL_MINUTES)