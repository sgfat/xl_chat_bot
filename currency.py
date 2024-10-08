import os
from aiohttp import ClientSession
from dotenv import load_dotenv
from config import logger

load_dotenv()

CUR_API_KEY = os.getenv('CUR_API_KEY')
CUR_API_URL_1 = os.getenv('CUR_API_URL_1')
CUR_API_URL_2 = os.getenv('CUR_API_URL_2')
CUR_API_LIST = os.getenv('CUR_API_LIST')


async def request_api(url) -> dict:
    async with ClientSession() as session:
        params = {'apikey': CUR_API_KEY, 'currencies': CUR_API_LIST}
        async with session.get(url, params=params) as response:
            data = await response.json()
    return data['data']


async def check_currency_rates(client, event) -> None:
    try:
        logger.debug('Sending requests to currencies API')
        rates = await request_api(CUR_API_URL_1)
        currencies = await request_api(CUR_API_URL_2)

        logger.debug('Sending reply with currencies')
        message_text = '1 USD =\n' + '\n'.join(
            f'{float(rate):,.2f} {currencies[cur]["code"]}'.replace(',', ' ')
            for cur, rate in rates.items()
        )
        await client.send_message(event.chat_id, message_text)

    except Exception as e:
        logger.error(f'An error occurred: {e}')
    finally:
        logger.debug('Currency rates request finished')
