import asyncio
import os
import sys
from asyncio import new_event_loop, set_event_loop

from pytz import utc
from dotenv import load_dotenv
from telegram.ext import MessageHandler, filters, Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Bot

from config import logger
from photos import check_photos
from movie import random_movie_link

load_dotenv()

TOKEN = os.getenv('TOKEN')


# TODO Change check_tokens function
def check_tokens() -> bool:
    """Checking tokens."""
    logger.debug('Checking tokens')
    tokens = {
        'TOKEN': TOKEN,
    }
    for token, token_value in tokens.items():
        if token_value is None:
            logger.critical(f"Can't find token:{token}")
            return False
    logger.debug('All tokens OK')
    return True


async def handle_words(update, context):
    """Listen words from chat."""
    message = update.message.text
    if 'ботя' not in message.lower():
        return
    if 'кино' in message.lower():
        logger.debug('Random movie link requested')
        await random_movie_link(update, context, type_m='movie')
    if 'сериал' in message.lower():
        logger.debug('Random movie link requested')
        await random_movie_link(update, context, type_m='tv-series')


def run_check_photos(bot: Bot):
    """Wrapper to run check_photos in an asyncio event loop."""
    loop = new_event_loop()
    set_event_loop(loop)
    loop.run_until_complete(check_photos(bot))
    loop.close()


def main() -> None:
    """Main function."""
    if not check_tokens():
        sys.exit("Program interrupted! Can't find tokens.")

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_words))

    scheduler = AsyncIOScheduler(timezone=utc)
    scheduler.add_job(lambda: run_check_photos(application.bot), trigger='interval', hours=13)
    scheduler.start()

    logger.debug('Bot started')

    application.run_polling()


if __name__ == '__main__':
    main()
