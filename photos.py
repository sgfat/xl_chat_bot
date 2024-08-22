import os
import json
import re

from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests import Session
from telegram import Bot, InputMediaPhoto

from config import logger

load_dotenv()

CHAT_ID = os.getenv('CHAT_ID')
LINKS_FILE = os.getenv('LINKS_FILE')
TIMESTAMP_FILE = os.getenv('TIMESTAMP_FILE')
TEMP_FOLDER = os.getenv('TEMP_FOLDER')
PHOTO_THREAD_ID = os.getenv('PHOTO_THREAD_ID')
VK_API_URL = os.getenv('VK_API_URL')
VK_API_TOKEN = os.getenv('VK_API_TOKEN')
VK_GROUP_ID = os.getenv('VK_GROUP_ID')

if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


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


async def send_files(bot: Bot, urls: list, caption=None) -> set:
    """Send all files to chat."""
    logger.debug('Sending files...')
    media = []
    media.extend(InputMediaPhoto(media=url) for url in urls)
    if media:
        try:
            logger.debug(f"Attempting to send {len(media)} files with caption: {caption}")
            await bot.send_media_group(
                caption=caption,
                chat_id=CHAT_ID,
                message_thread_id=PHOTO_THREAD_ID,
                media=media,
                pool_timeout=60
            )
            logger.debug(f"{len(urls)} files sent successfully")
        except Exception as e:
            logger.error(f"Failed to send media group: {e}")
    return set(urls)


def parse_photos_links() -> set:
    """Parse photos links from category page."""
    logger.debug('Start parsing links...')
    with Session() as s:
        cookies = dict(nude='true')
        response = s.get('https://35photo.pro/genre_98/', cookies=cookies)
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = set()
    for a in soup.find_all('a', href=True):
        if 'href-mobile' in a.attrs:
            urls.add(a['href-mobile'])
            if len(urls) == 10:
                break
    logger.debug('Links parsed')
    return urls


async def check_35_photos(bot: Bot) -> None:
    """Main auto check new photos repeating function."""
    logger.debug('Begin checking 35photo photos...')
    try:
        new_links = parse_photos_links()
        known_links = load_links('35_photo_links')
        if new_links := new_links - known_links:
            save_links('35_photo_links', new_links)
            await send_files(bot, list(new_links), '35photo.ru')
        else:
            logger.debug('No new links')
    except Exception as e:
        logger.error(f'An error occurred: {e}')
    finally:
        logger.debug('Finish checking photos')


def vk_api_request() -> dict:
    """Request to VK API."""
    logger.debug("Sending request to VK API...")
    try:
        with Session() as s:
            params = {'access_token': VK_API_TOKEN,
                      'v': '5.199',
                      'owner_id': VK_GROUP_ID,
                      'count': '10'}
            response = s.get(VK_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug("VK API request successful")
            return data['response']['items']
    except Exception as e:
        logger.error(f"Error during VK API request: {e}")
        return {}


async def check_bravo_photos(bot: Bot) -> None:
    """Check photos from Bravo VK group."""
    logger.debug('Begin checking Bravo photos')
    known_posts = load_links('bravo_posts')
    data = vk_api_request()
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
            await send_files(bot, media, caption)
        else:
            logger.debug('No new links')

    save_links('bravo_posts', known_posts)
