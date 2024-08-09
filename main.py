import asyncio
import os
import sys

from dotenv import load_dotenv
from telegram.ext import MessageHandler, filters, Application, CommandHandler

from config import logger
from photos import check_photos
from movie import random_movie_link
from utils import send_message

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


async def start(update, context):
    await update.message.reply_text('Bot Started!')


async def send_startup_message(application: Application) -> None:
    """Send startup message."""
    await send_message(application.bot,
                       f'Bot is ready for work.',
                       short_log=True)


async def handle_words(update, context):
    message = update.message.text

    if 'ботя' not in message.lower():
        return
    if 'кино' in message.lower():
        logger.debug('Random movie link requested')
        await random_movie_link(update, context, type_m='movie')
    if 'сериал' in message.lower():
        logger.debug('Random movie link requested')
        await random_movie_link(update, context, type_m='tv-series')


def main() -> None:
    """Main function."""
    if not check_tokens():
        sys.exit("Program interrupted! Can't find tokens.")

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check_photos", check_photos))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_words))
    logger.debug('Bot started')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_startup_message(application))

    application.run_polling()


if __name__ == '__main__':
    main()
