import os

import aiohttp
from aiohttp import ClientSession
from dotenv import load_dotenv

from config import logger

load_dotenv()

X_API_URL = os.getenv('X_API_URL')
X_API_KEY = os.getenv('X_API_KEY')


# TODO fix for PEP-8
async def random_movie_link(update, context, type_m):
    genre_mapping = {1: "Фильм", 2: "Сериал", 3: "Мультфильм",
                     4: "Аниме", 5: "Мультсериал", 6: "ТВ-Шоу"}
    logger.debug(f'Random {type_m} link requested.')
    try:
        async with ClientSession() as session:
            headers = {'X-API-KEY': X_API_KEY}
            url = f'{X_API_URL}movie/random?rating.kp=7-10&type={type_m}'
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                description = data['description']
                poster = data['poster']['url']
                poster_path = await download_poster(poster)
                if data['videos'] and data['videos']['trailers']:
                    trailer_urls = '\n'.join(x['url'] for x in
                                             data['videos']['trailers'])
                else:
                    trailer_urls = None
                # await context.bot.send_messsage(
                await update.message.reply_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(poster_path, 'rb'),
                    caption=f'{genre_mapping[data["typeNumber"]]}: '
                            f'{data["name"]} ({data["year"]}, '
                            f'{", ".join(c["name"] for c in data["countries"])})\n'
                            f'Жанр: {", ".join(g["name"] for g in data["genres"])}\n'
                            f'КП: {data["rating"]["kp"]} '
                            f'IMDB: {data["rating"]["imdb"]}\n\n'
                            f'{"Нет описания" if description is None else description}\n\n'
                    # f'Трейлеры:\n{"Нет трейлеров" if trailer_urls is None else trailer_urls}'
                    # f'{", ".join(x["url"] for x in data["videos"]["trailers"])}'
                )

                logger.debug('Random movie link created')
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'poster_path' in locals():
            os.remove(poster_path)


async def download_poster(poster_url: str) -> str:
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(poster_url) as response:
            if response.status == 200:
                poster_path = "temp_poster.jpg"
                with open(poster_path, 'wb') as f:
                    f.write(await response.read())
                return poster_path
