import asyncio
import os
import json
import re

from dotenv import load_dotenv
from aiohttp import ClientSession
from telethon import TelegramClient
from telethon.tl.types import InputMediaPhotoExternal
from config import logger

load_dotenv()

CHAT_ID = int(os.getenv('CHAT_ID'))
LINKS_FILE = os.getenv('LINKS_FILE')
TIMESTAMP_FILE = os.getenv('TIMESTAMP_FILE')
TEMP_FOLDER = os.getenv('TEMP_FOLDER')
PHOTO_THREAD_ID = int(os.getenv('PHOTO_THREAD_ID'))
VK_API_URL = os.getenv('VK_API_URL')
VK_API_TOKEN = os.getenv('VK_API_TOKEN')
VK_GROUP_ID = os.getenv('VK_GROUP_ID')

if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

retries = 3
initial_sleep_time = 5


def load_links(key: str) -> set:
    """Load last links from LINKS_FILE under a specific key."""
    logger.debug(f'Loading last links for {key}...')
    try:
        with open(LINKS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get(key, []))
    except FileNotFoundError:
        return set()


def save_links(key: str, links: set) -> None:
    """Save last links to LINKS_FILE under a specific key."""
    try:
        with open(LINKS_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data[key] = list(links)
    with open(LINKS_FILE, 'w') as f:
        json.dump(data, f)
        logger.debug(f'Last links saved for {key}')


async def send_files(client: TelegramClient, urls: list, caption=None) -> set:
    """Send all files to chat with retries."""
    logger.debug('Sending files...')

    if urls:
        for attempt in range(retries):
            try:
                logger.debug(f"Attempting to send {len(urls)} files with caption: {caption}")
                await client.send_message(
                    CHAT_ID,
                    file=urls,
                    message=caption,
                    reply_to=PHOTO_THREAD_ID
                )
                logger.debug(f"{len(urls)} files sent successfully")
                break
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Failed to send media group after {retries} attempts: {e}")
                else:
                    sleep_time = initial_sleep_time * (2 ** attempt)
                    logger.debug(f"Retrying in {sleep_time} seconds...")
                    await asyncio.sleep(sleep_time)

    return set(urls)


async def vk_api_request() -> dict:
    """Request to VK API."""
    logger.debug("Sending request to VK API...")
    try:
        async with ClientSession() as session:
            params = {'access_token': VK_API_TOKEN,
                      'v': '5.199',
                      'owner_id': VK_GROUP_ID,
                      'count': '10'}
            async with session.get(VK_API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug("VK API request successful")
                return data['response']['items']
    except Exception as e:
        logger.error(f"Error during VK API request: {e}")
        return {}


async def check_bravo_photos(client: TelegramClient) -> None:
    """Check photos from Bravo VK group."""
    logger.debug('Begin checking Bravo photos')
    known_posts = load_links('bravo_posts')
    data = await vk_api_request()
    for post in data:
        if post['id'] in known_posts:
            continue
        if post.get('copy_history', None):
            continue
        if post.get('is_pinned', None):
            continue

        known_posts.add(post['id'])
        if media := [
            attachment['photo']['orig_photo']['url']
            for attachment in post['attachments']
            if attachment['type'] == 'photo'
        ]:
            text = post['text']
            result = re.sub(
                r'\[(club|id)\d+\|([^\]]+)\]', r'\2', text
            )
            caption = result or None
            await send_files(client, media, caption)
        else:
            logger.debug('No new links')
        await asyncio.sleep(5)

    save_links('bravo_posts', known_posts)
