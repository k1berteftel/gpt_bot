import asyncio
import random
import logging

from aiogram import Bot
from aiogram.types import Message


logger = logging.getLogger(__name__)


def _progress_bar(percent: int) -> str:
    return "🟩" * (percent // 10) + "⬜️" * (10 - percent // 10) + f" {percent}%"


def _progress_text(percent: int):
    bar = _progress_bar(percent)
    if percent < 30:
        text = '📝Принял ваш запрос...'
    elif percent < 50:
        text = '⚡️Анализ...'
    elif percent < 70:
        text = '🔄 Генерация...'
    elif percent < 90:
        text = '🧠 Обработка...'
    else:
        text = '💬Возвращаю ответ...'
    return text + '\n' + bar


async def quick_generation(msg: Message):
    for p in [80, 90, 100]:
        text = _progress_text(p)
        await msg.edit_text(text)
        await asyncio.sleep(0.25)


async def process_generate(msg: Message):
    for p in [5, 20, 30, 40, 55, 70, 75]:
        text = _progress_text(p)
        await msg.edit_text(text)
        await asyncio.sleep(2.3)


async def generate_wrapper(func, bot: Bot, user_id: int, *args) -> any:
    await bot.send_chat_action(user_id, "typing")
    msg = await bot.send_message(
        chat_id=user_id,
        text=_progress_text(1)
    )
    task = asyncio.create_task(process_generate(msg))
    try:
        result = await func(*args)
    except Exception as err:
        logger.error(f'Ошибка во время генерации: {err}')
        result = {'error': str(err)}
    finally:
        task.cancel()
        await quick_generation(msg)
        await msg.delete()
    return result
