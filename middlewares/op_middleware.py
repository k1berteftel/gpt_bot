import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram_dialog import DialogManager, StartMode
from aiogram.types import TelegramObject, User, Chat
from database.action_data_class import DataInteraction
from states.state_groups import SubSG

logger = logging.getLogger(__name__)


class OpMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session: DataInteraction = data.get('session')
        user: User = data.get('event_from_user')
        chat: Chat = data.get('event_chat')
        channels = await session.get_op()
        if not channels:
            return await handler(event, data)
        bot: Bot = data.get('bot')
        dialog_manager: DialogManager = data.get('dialog_manager')
        user: User = data.get('event_from_user')
        left = False
        left_channels = []
        for channel in channels:
            member = await bot.get_chat_member(chat_id=channel.chat_id, user_id=user.id)
            print(dialog_manager.current_context().state)
            if dialog_manager.current_context().state != SubSG.start:
                if member.status == 'left':
                    left_channels.append(channel.id)
                    left = True
        if left:
            while dialog_manager.has_context():
                await dialog_manager.done()
            await dialog_manager.start(SubSG.start, data={'channels': left_channels}, mode=StartMode.RESET_STACK)
            return

        return await handler(event, data)