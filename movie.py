import os
from aiohttp import ClientSession
from dotenv import load_dotenv
from config import logger

load_dotenv()

X_API_URL = os.getenv('X_API_URL')
X_API_KEY = os.getenv('X_API_KEY')


async def download_poster(poster_url: str) -> str:
    async with ClientSession(trust_env=True) as session:
        async with session.get(poster_url) as response:
            if response.status == 200:
                poster_path = "temp_poster.jpg"
                with open(poster_path, 'wb') as f:
                    f.write(await response.read())
                return poster_path


async def random_movie_link(client, event, type_m):
    genre_mapping = {
        1: "Фильм",
        2: "Сериал",
        3: "Мультфильм",
        4: "Аниме",
        5: "Мультсериал",
        6: "ТВ-Шоу"
    }

    try:
        async with ClientSession() as session:
            headers = {'X-API-KEY': X_API_KEY}
            url = f'{X_API_URL}{type_m}'
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

                description = data.get('description', 'Нет описания')
                poster = data['poster']['url']
                poster_path = await download_poster(poster)

                videos = data.get('videos', {})
                trailers = videos.get('trailers', [])
                trailer_urls = '\n'.join(x.get('url', '') for x in trailers if x.get('url'))

                caption = (
                    f'{genre_mapping.get(data["typeNumber"], "Неизвестный жанр")}: '
                    f'{data["name"]} ({data["year"]}, '
                    f'{", ".join(c["name"] for c in data["countries"])})\n'
                    f'Жанр: {", ".join(g["name"] for g in data["genres"])}\n'
                    f'КП: {data["rating"]["kp"]} '
                    f'IMDB: {data["rating"]["imdb"]}\n\n'
                    f'{description}\n\n'
                    f'Трейлеры:\n{trailer_urls or "Нет трейлеров"}'
                )

                if len(caption) > 1024:
                    caption = f'{caption[:1021]}...'
                    logger.warning("Caption too long, cut to 1024 symbols")

                await client.send_file(
                    event.chat_id,
                    file=poster_path,
                    caption=caption,
                    force_document=False,
                    reply_to=event.message.id,
                )

                logger.debug(f'Random {type_m} link created')

    except Exception as e:
        logger.error(f'An error occurred: {e}')

    finally:
        if 'poster_path' in locals():
            os.remove(poster_path)
        logger.debug('Random movie link processing finished')