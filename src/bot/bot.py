import asyncio
import logging
import contextlib
import inspect
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from src.config import TELEGRAM_BOT_TOKEN
from src.bot.commands import register_all_commands
from src.bot.commands_list import commands
from src.library.login import login_and_get_sid
from src.library.alert_monitor import start_alert_monitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_club_mappings(application):
    from src.database import db_manager
    from src.library.get_all_club_limits import get_all_club_limits
    
    try:
        chat_club_mapping = db_manager.get_chat_club_mapping()
        application.bot_data["chat_club_map"] = chat_club_mapping
        logger.info(f"Loaded {len(chat_club_mapping)} chat-club mappings")
        
        connect_sid = application.bot_data.get("sid")
        if connect_sid:
            club_data = await get_all_club_limits(connect_sid)
            if club_data and club_data.DATA:
                club_backend_mapping = {}
                for club in club_data.DATA:
                    display_id = int(club.f1)
                    backend_id = int(club.cno)
                    club_backend_mapping[display_id] = backend_id
                
                application.bot_data["club_id_map"] = club_backend_mapping
                logger.info(f"Loaded {len(club_backend_mapping)} club-backend mappings")
            else:
                logger.warning("No club data received from API")
                application.bot_data["club_id_map"] = {}
        else:
            logger.warning("No SID available for club-backend mapping")
            application.bot_data["club_id_map"] = {}
            
    except Exception as e:
        logger.error(f"Failed to load club mappings: {e}")
        application.bot_data["chat_club_map"] = {}
        application.bot_data["club_id_map"] = {}

async def map_club_id(display_id: int, context) -> int:
    if (context.application.bot_data.get("club_id_map") is None or
            display_id not in context.application.bot_data["club_id_map"]):
        await load_club_mappings(context.application)
    
    club_id_map = context.application.bot_data.get("club_id_map", {})
    if display_id not in club_id_map:
        raise ValueError(f"No backend_id found for display_id: {display_id}")
    
    return club_id_map[display_id]

def get_chat_club_id(chat_id: int, context) -> int:
    chat_club_map = context.application.bot_data.get("chat_club_map", {})
    if chat_id not in chat_club_map:
        raise ValueError(f"No club_id found for chat_id: {chat_id}")
    return chat_club_map[chat_id]

async def ensure_sid(app):
    try:
        sid = await login_and_get_sid()
        app.bot_data["sid"] = sid
        logger.info("Session established")
    except Exception as e:
        logger.error(f"Session failed: {e}")
        raise

async def sid_refresher(application):
    while True:
        try:
            await asyncio.sleep(300)
            
            sid = await login_and_get_sid()
            application.bot_data["sid"] = sid
            
            logger.info("Refreshing club mappings...")
            await load_club_mappings(application)
            logger.info("Club mappings refreshed")
        except Exception as e:
            logger.exception("Failed to refresh sid: %s", e)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None))
    app.add_error_handler(error_handler)
    
    register_all_commands(app)
    await app.bot.set_my_commands(commands)
    
    await app.initialize()
    await ensure_sid(app)
    
    logger.info("Loading club mappings...")
    await load_club_mappings(app)
    logger.info("Club mappings loaded")
    
    await app.start()
    
    try:
        await app.updater.start_polling()
    except Exception as e:
        if "Conflict" in str(e):
            logger.error("Another bot instance is already running. Please stop it first.")
            return
        raise
    
    asyncio.create_task(start_alert_monitoring(app.bot, app))
    asyncio.create_task(sid_refresher(app))
    
    logger.info("Bot started")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())