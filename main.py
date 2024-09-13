import os

from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from pytz import utc

from config import logger, PHOTO_CHECK_PERIOD
from photos import check_bravo_photos, check_35_photos
from movie import random_movie_link
from currency import check_currency_rates
from gpt import ask_chatgpt

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('TOKEN')

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@client.on(events.NewMessage(pattern=r'^ботя\s+(\w+)'))
async def handle_words(event):
    """Listen words from chat."""
    request = event.pattern_match.group(1).lower()

    if 'кино' in request:
        logger.debug('Random movie link requested')
        await random_movie_link(client, event, type_m='movie')
    elif 'сериал' in request:
        logger.debug('Random tv-show link requested')
        await random_movie_link(client, event, type_m='tv-series')
    elif 'аниме' in request or 'анимэ' in request:
        logger.debug('Random anime link requested')
        await random_movie_link(client, event, type_m='anime')
    elif 'вопрос' in request:
        logger.debug('GPT request')
        await ask_chatgpt(client, event)
    elif 'курс' in request:
        logger.debug('Currency rates requested')
        await check_currency_rates(client, event)


async def run_check_photos():
    """Wrapper to run check_photos periodically."""
    await check_bravo_photos(client)
    await check_35_photos(client)


def main():
    """Main function."""
    scheduler = AsyncIOScheduler(timezone=utc)
    scheduler.add_job(
        run_check_photos,
        trigger='interval',
        hours=PHOTO_CHECK_PERIOD,
        max_instances=2
    )
    scheduler.start()

    logger.debug('Bot started')
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
