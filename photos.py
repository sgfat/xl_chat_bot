import os
import json
import asyncio
from datetime import datetime, timedelta

import aiohttp
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto, Update
from telegram.ext import ContextTypes

from config import PHOTO_RETRY_PERIOD, logger

load_dotenv()

CHAT_ID = os.getenv('CHAT_ID')
LINKS_FILE = os.getenv('LINKS_FILE')
TIMESTAMP_FILE = os.getenv('TIMESTAMP_FILE')
TEMP_FOLDER = os.getenv('TEMP_FOLDER')
PHOTO_THREAD_ID = os.getenv('PHOTO_THREAD_ID')

if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


def load_links() -> set:
    """Load last links from LINKS_FILE."""
    logger.debug('Loading last links...')
    try:
        with open(LINKS_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def save_links(links: set) -> None:
    """Save last links to LINKS_FILE."""
    with open(LINKS_FILE, 'w') as f:
        json.dump(list(links), f)
        logger.debug('Last links saved')


def load_last_run_time() -> datetime | None:
    """Load last timestamp from TIMESTAMP_FILE."""
    logger.debug('Loading last timestamp...')
    if os.path.exists(TIMESTAMP_FILE):
        with open(TIMESTAMP_FILE, 'r') as f:
            timestamp_str = f.read().strip()
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
    return None


def save_last_run_time() -> None:
    """Save last timestamp to TIMESTAMP_FILE."""
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(datetime.now().isoformat())
        logger.debug('Timestamp saved')


async def download_file(url: str):
    """Download files to TEMP_FOLDER."""
    logger.debug(f'Downloading file {url}')
    file_name = os.path.join(TEMP_FOLDER, url.split('/')[-1])
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_name, 'wb') as f:
                    f.write(await response.read())
                return file_name


async def send_files(bot: Bot, urls: list) -> set:
    """Send all files to chat."""
    logger.debug('Sending files...')
    media = []
    for url in urls:
        file_path = await download_file(url)
        media.append(InputMediaPhoto(open(file_path, 'rb')))
    if media:
        await bot.send_media_group(chat_id=CHAT_ID,
                                   # message_thread_id=PHOTO_THREAD_ID,
                                   media=media)
    return set(urls)


def clear_temp_folder() -> None:
    """Clear TEMP_FOLDER."""
    for file in os.listdir(TEMP_FOLDER):
        file_path = os.path.join(TEMP_FOLDER, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    logger.debug('Temp folder cleared')


def parse_photos_links() -> set:
    """Parse photos links from category page."""
    logger.debug('Start parsing links...')
    with requests.Session() as s:
        cookies = dict(nude='true')
        response = s.get('https://35photo.pro/genre_98/', cookies=cookies)
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = set()
    for a in soup.find_all('a', href=True):
        if 'href-mobile' in a.attrs:
            urls.add(a['href-mobile'])
            if len(urls) == 3:
                break
    logger.debug('Links parsed')
    return urls


# TODO Add checking already running function
# TODO Add exceptions
async def check_photos(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main auto check new photos repeating function."""
    logger.debug('Begin checking photos...')
    while True:
        try:
            last_run_time = load_last_run_time()
            if (last_run_time and
                    datetime.now() - last_run_time > timedelta(hours=24)):
                # new_links = parse_photos_links()
                new_links = [
                    'https://parsinger.ru/legal/img/1/1/1_1.jpg', 'https://parsinger.ru/legal/img/1/1/1_2.jpg',
                    'https://parsinger.ru/legal/img/1/1/1_3.jpg', 'https://parsinger.ru/legal/img/1/1/1_4.jpg'
                ]
                known_links = load_links()
                new_links = set(new_links) - known_links
                if new_links:
                    await send_files(context.bot, list(new_links))
                    save_links(new_links)
                    save_last_run_time()
                    clear_temp_folder()
                    logger.debug('Finish checking photos')
                else:
                    logger.debug('No new links')
            else:
                logger.debug('Skipped checking')
        finally:
            await asyncio.sleep(PHOTO_RETRY_PERIOD)
