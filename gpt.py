import os

import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv
from config import GPT_CONTENT, logger

load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')


async def ask_chatgpt(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPEN_AI_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': GPT_CONTENT},
            {'role': 'user', 'content': update.message.text}
        ],
        'max_tokens': 200
    }

    response = requests.post(url, json=data, headers=headers)
    response_json = response.json()
    print(response_json)
    reply = response_json['choices'][0]['message']['content']
    try:
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.debug(f'Error: {e}')
        await update.message.reply_text(f'Ошибка: {e}')
    else:
        logger.debug('GPT answer sent')
