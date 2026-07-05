import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Import handlers (we will create these next)
from bot.handlers.menu import menu_router
from bot.handlers.squads import squads_router
from bot.handlers.predictions import predictions_router
from bot.handlers.onboarding import router as onboarding_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    token = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    if token == "YOUR_BOT_TOKEN_HERE":
        logger.warning("BOT_TOKEN is not set in environment variables.")
        
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(onboarding_router)
    dp.include_router(menu_router)
    dp.include_router(squads_router)
    dp.include_router(predictions_router)

    logger.info("Deleting any existing webhooks...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("Starting bot in Long Polling mode...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
