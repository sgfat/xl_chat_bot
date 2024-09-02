import os
import aiohttp
from telethon import events
from dotenv import load_dotenv
from config import GPT_CONTENT, logger

load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')


async def ask_chatgpt(client, event) -> None:
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPEN_AI_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': GPT_CONTENT},
            {'role': 'user', 'content': event.message.message}
        ],
        'max_tokens': 200
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                response.raise_for_status()
                response_json = await response.json()

        reply = response_json['choices'][0]['message']['content']

        await client.send_message(event.chat_id, reply, parse_mode='Markdown')

    except Exception as e:
        logger.error(f'Error: {e}')
        await client.send_message(event.chat_id, f'Ошибка: {e}')

    else:
        logger.debug('GPT answer sent')
