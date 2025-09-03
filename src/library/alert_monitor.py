# src/library/alert_monitor.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from telegram import Bot
from telegram.error import TelegramError

from .get_all_club_limits import get_all_club_limits
from ..utils.roles import user_roles

logger = logging.getLogger(__name__)

# ===== ALERT THRESHOLDS - CUSTOMIZE THESE VALUES =====
LOSS_LIMIT_WARNING_PERCENT = 90.0    # Alert when loss reaches 90% of limit
WIN_LIMIT_WARNING_PERCENT = 90.0     # Alert when win reaches 90% of limit
PNL_NEGATIVE_THRESHOLD = -1000.0     # Alert when P&L goes below -$1000
CHECK_INTERVAL_MINUTES = 1          # Check every 1 minutes
ALERT_COOLDOWN_MINUTES = 5          # Don't spam same alert within 30 minutes
# =====================================================

# Global state for alert cooldowns
last_alert_times: Dict[str, datetime] = {}
alert_cooldown = timedelta(minutes=ALERT_COOLDOWN_MINUTES)

def parse_numeric_value(value_str: str) -> float:
    """Parse numeric values from club data strings"""
    if not value_str or value_str.strip() == "":
        return 0.0
    try:
        return float(str(value_str).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0

def should_send_alert(club_id: int, alert_type: str) -> bool:
    """Check if enough time has passed since last alert"""
    key = f"{club_id}_{alert_type}"
    last_alert = last_alert_times.get(key)
    if not last_alert:
        return True
    return datetime.now() - last_alert > alert_cooldown

def update_alert_time(club_id: int, alert_type: str):
    """Update the last alert time for this club and alert type"""
    key = f"{club_id}_{alert_type}"
    last_alert_times[key] = datetime.now()

def get_alert_recipients(club_id: int) -> List[int]:
    """Get the list of user IDs who should receive alerts for this club"""
    recipients = []
    
    for user_role in user_roles:
        user_id = user_role["userId"]
        role = user_role["role"]
        clubs = user_role.get("clubs", [])
        
        # Union Heads get all alerts
        if role == "Union Head":
            recipients.append(user_id)
        # Region Heads get alerts for clubs in their region
        elif role == "Region Head" and club_id in clubs:
            recipients.append(user_id)
        # Club Owners get alerts for their specific clubs
        elif role == "Club Owner" and club_id in clubs:
            recipients.append(user_id)
    
    return list(set(recipients))  # Remove duplicates

async def send_alert(bot: Bot, message: str, user_id: int, club_id: int):
    """Send an alert to a specific user"""
    try:
        await bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Alert sent to user {user_id} for club {club_id}")
    except TelegramError as e:
        logger.error(f"Failed to send alert to user {user_id}: {e}")

async def check_and_send_alerts(bot: Bot, connect_sid: str) -> int:
    """Check all clubs and send alerts"""
    try:
        # Fetch all club data
        club_data = await get_all_club_limits(connect_sid)
        if not club_data or not club_data.DATA:
            logger.warning("No club data received for alert monitoring")
            return 0
        
        total_alerts_sent = 0
        
        # Analyze each club
        for club in club_data.DATA:
            club_id = club.cno
            
            # Parse numeric values
            ring_pnl = parse_numeric_value(club.f4)
            tournament_pnl = parse_numeric_value(club.f5)
            loss_limit = parse_numeric_value(club.f6)
            win_limit = parse_numeric_value(club.f7)
            
            # Check loss limit warning (only if loss limit is set and there's a loss)
            if loss_limit > 0 and ring_pnl < 0:
                loss_percentage = abs(ring_pnl) / loss_limit * 100
                if loss_percentage >= LOSS_LIMIT_WARNING_PERCENT and should_send_alert(club_id, "loss_limit"):
                    message = f"🚨 <b>LOSS LIMIT WARNING</b>\n\n" \
                             f"🏢 <b>Club:</b> {club.f2}\n" \
                             f"🆔 <b>Club ID:</b> {club.f1}\n" \
                             f"👤 <b>Owner:</b> {club.f3}\n\n" \
                             f"💰 <b>Current Loss:</b> ${abs(ring_pnl):,.2f}\n" \
                             f"📊 <b>Loss Limit:</b> ${loss_limit:,.2f}\n" \
                             f"📈 <b>Usage:</b> {loss_percentage:.1f}%"
                    
                    recipients = get_alert_recipients(club_id)
                    for user_id in recipients:
                        await send_alert(bot, message, user_id, club_id)
                        total_alerts_sent += 1
                    
                    update_alert_time(club_id, "loss_limit")
            
            # Check win limit warning (only if win limit is set and there's a win)
            if win_limit > 0 and ring_pnl > 0:
                win_percentage = ring_pnl / win_limit * 100
                if win_percentage >= WIN_LIMIT_WARNING_PERCENT and should_send_alert(club_id, "win_limit"):
                    message = f"🎯 <b>WIN LIMIT WARNING</b>\n\n" \
                             f"🏢 <b>Club:</b> {club.f2}\n" \
                             f"🆔 <b>Club ID:</b> {club.f1}\n" \
                             f"👤 <b>Owner:</b> {club.f3}\n\n" \
                             f"💰 <b>Current Win:</b> ${ring_pnl:,.2f}\n" \
                             f"📊 <b>Win Limit:</b> ${win_limit:,.2f}\n" \
                             f"📈 <b>Usage:</b> {win_percentage:.1f}%"
                    
                    recipients = get_alert_recipients(club_id)
                    for user_id in recipients:
                        await send_alert(bot, message, user_id, club_id)
                        total_alerts_sent += 1
                    
                    update_alert_time(club_id, "win_limit")
            
            # Check for significant negative P&L
            total_pnl = ring_pnl + tournament_pnl
            if total_pnl <= PNL_NEGATIVE_THRESHOLD and should_send_alert(club_id, "negative_pnl"):
                message = f"📉 <b>SIGNIFICANT LOSS ALERT</b>\n\n" \
                         f"🏢 <b>Club:</b> {club.f2}\n" \
                         f"🆔 <b>Club ID:</b> {club.f1}\n" \
                         f"👤 <b>Owner:</b> {club.f3}\n\n" \
                         f"💰 <b>Total P&L:</b> ${total_pnl:,.2f}\n" \
                         f"🎰 <b>Ring Game P&L:</b> ${ring_pnl:,.2f}\n" \
                         f"🏆 <b>Tournament P&L:</b> ${tournament_pnl:,.2f}"
                
                recipients = get_alert_recipients(club_id)
                for user_id in recipients:
                    await send_alert(bot, message, user_id, club_id)
                    total_alerts_sent += 1
                
                update_alert_time(club_id, "negative_pnl")
            

        
        logger.info(f"Alert check completed. Sent {total_alerts_sent} alerts.")
        return total_alerts_sent
        
    except Exception as e:
        logger.error(f"Error in alert monitoring: {e}")
        return 0

async def start_alert_monitoring(bot: Bot, application):
    """Start the continuous alert monitoring loop"""
    logger.info("Starting alert monitoring service...")
    
    # Wait for SID to be available (login process takes time)
    logger.info("Waiting for SID to be available...")
    while True:
        connect_sid = application.bot_data.get("sid")
        if connect_sid:
            logger.info("✅ SID available, starting alert monitoring")
            break
        await asyncio.sleep(5)  # Check every 5 seconds for SID
    
    while True:
        try:
            # Get SID from application
            connect_sid = application.bot_data.get("sid")
            if connect_sid:
                await check_and_send_alerts(bot, connect_sid)
            else:
                logger.warning("No SID available for alert monitoring")
            
            # Check at configured interval
            await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
            
        except asyncio.CancelledError:
            logger.info("Alert monitoring cancelled")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying