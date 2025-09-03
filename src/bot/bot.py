# src/bot/bot.py
import asyncio
import logging
import contextlib
import inspect
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from src.config import TELEGRAM_BOT_TOKEN
from src.bot.commands import register_all_commands
from src.bot.commands_list import commands
from src.library.login import login_and_get_sid  # may be sync or async
from src.library.alert_monitor import start_alert_monitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- utils: call login_and_get_sid whether sync or async ----------
async def _get_sid() -> str:
    if inspect.iscoroutinefunction(login_and_get_sid):
        return await login_and_get_sid()    # async version
    return await asyncio.to_thread(login_and_get_sid)  # sync (requests) version

# ---------- startup fetch (proactive) ----------
async def ensure_sid(application: Application) -> None:
    try:
        if application.bot_data.get("sid") is None:
            logger.info("🔄 Initial connect.sid fetch...")
            application.bot_data["sid"] = await _get_sid()
            logger.info("✅ Initial sid ready")
    except Exception as e:
        # DO NOT let this kill startup
        logger.exception("❌ Initial SID fetch failed: %s", e)
        application.bot_data["sid"] = None

# ---------- per-update guard (reactive) ----------
async def sid_inject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.application.bot_data.get("sid") is None:
        try:
            context.application.bot_data["sid"] = await _get_sid()
        except Exception as e:
            logger.exception("❌ Could not obtain sid on-demand: %s", e)

# ---------- background refresher (wait once before first run) ----------
async def sid_refresher(application: Application, interval_seconds: int = 50 * 60) -> None:
    try:
        # wait BEFORE first refresh to avoid double-fetch at startup
        await asyncio.sleep(interval_seconds)
        while True:
            try:
                logger.info("🔄 Refreshing connect.sid...")
                application.bot_data["sid"] = await _get_sid()
                logger.info("✅ New sid fetched")
            except Exception as e:
                logger.exception("❌ Failed to refresh sid: %s", e)
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("🛑 SID refresher cancelled")
        raise
    except Exception as e:
        logger.exception("❌ SID refresher error: %s", e)
        raise

# ---------- error logging so hidden exceptions don't stop the app ----------
async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("⚠️ Handler/Job error", exc_info=context.error)

# ---------- app bootstrap (YOUR original lifecycle) ----------
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.bot_data["sid"] = None

    # run sid_inject BEFORE everything else (safety net)
    app.add_handler(MessageHandler(filters.ALL, sid_inject), group=-1000)

    # register your commands
    register_all_commands(app)
    
    # set bot commands list for Telegram UI
    await app.bot.set_my_commands(commands)

    # attach global error handler
    app.add_error_handler(_on_error)

    # background refresher (with initial delay)
    refresher_task = asyncio.create_task(sid_refresher(app, interval_seconds=50 * 60))
    
    # start alert monitoring
    alert_task = asyncio.create_task(start_alert_monitoring(app.bot, app))

    try:
        await app.initialize()
        await ensure_sid(app)              # fetch once; exceptions handled internally
        await app.start()
        await app.updater.start_polling()
        logger.info("🤖 Bot is running and ready to receive commands")
        
        # Keep the bot running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("🛑 Bot shutdown requested")
            raise
    except asyncio.CancelledError:
        logger.info("🛑 Bot shutdown requested")
    except Exception as e:
        logger.exception("❌ Bot error: %s", e)
        raise
    finally:
        logger.info("🔄 Shutting down bot...")
        alert_task.cancel()
        refresher_task.cancel()
        try:
            await alert_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Error cancelling alert task: %s", e)
        try:
            await refresher_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Error cancelling refresher task: %s", e)
        
        try:
            await app.stop()
        except Exception as e:
            logger.warning("Error stopping application: %s", e)
        logger.info("✅ Bot shutdown complete")

if __name__ == "__main__":
    # IMPORTANT: do not wrap anything else around this; let your main drive the loop
    asyncio.run(main())
