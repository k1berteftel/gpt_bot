import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, User, InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.action_data_class import DataInteraction
from config_data.config import load_config, Config

config: Config = load_config()
logger = logging.getLogger(__name__)


async def _remind_func(user_id: int, text: str, keyboard: InlineKeyboardMarkup, days: int, bot: Bot):
    await asyncio.sleep(60*60*24*days)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard
        )
    except Exception:
        ...


class RemindMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_from_user: User = data.get('event_from_user')

        if event_from_user is None:
            return await handler(event, data)

        session: DataInteraction = data.get('session')
        await session.set_activity(user_id=event_from_user.id)

        bot: Bot = data.get('bot')
        task_name_2 = f'{event_from_user.id}_7_remind'

        for task in asyncio.all_tasks():
            if task.get_name() in [task_name_2]:
                task.cancel()

        text_2 = ('Ты забыл обо мне? 😢\n\nА я тут готов помочь хоть сейчас — сделать генерацию из тренда или '
                  'решить любую задачу \n\nДавай попробуем еще раз🙌🏻')
        keyboard_2 = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Забрать 10 💎', callback_data='get_free_crystals')]]
        )
        task_2 = asyncio.create_task(_remind_func(event_from_user.id, text_2, keyboard_2, 7, bot))
        task_2.set_name(task_name_2)

        result = await handler(event, data)
        return result
