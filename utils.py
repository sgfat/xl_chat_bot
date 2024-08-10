import telegram
from exceptions import BotSendMessageError
import os
from dotenv import load_dotenv

load_dotenv()

CHAT_ID = os.getenv('CHAT_ID')


async def send_message(bot, message, short_log=False, **kwargs) -> None:
    """Send message to Telegram."""
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, **kwargs)
    except telegram.error.TelegramError as error:
        raise BotSendMessageError(f'Send message failure: {error}') from error
    else:
        if not short_log:
            print(f'Bot send message: "{message}"')
        else:
            print('Bot send message.')