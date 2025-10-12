import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, User, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.action_data_class import DataInteraction
from config_data.config import load_config, Config


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: float = 1.0):
        self.latency = latency
        self.album_data: dict[str, dict] = {}
        self.lock = asyncio.Lock()

    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any],
    ) -> Any:

        # Если не медиагруппа
        if not event.media_group_id:
            data["album"] = [event]
            return await handler(event, data)

        group_id = event.media_group_id

        async with self.lock:
            if group_id not in self.album_data:
                # Первое сообщение в группе - создаем запись и запускаем обработку
                self.album_data[group_id] = {
                    "messages": [event],
                    "event": asyncio.Event(),
                    "processed": False
                }

                # Запускаем задачу для обработки группы
                asyncio.create_task(self._process_media_group(group_id, handler, data))
            else:
                # Добавляем сообщение в существующую группу
                self.album_data[group_id]["messages"].append(event)
                # Сортируем по message_id для правильного порядка
                self.album_data[group_id]["messages"].sort(key=lambda x: x.message_id)

        # Для всех сообщений медиагруппы, кроме первого, не вызываем хендлер
        return

    async def _process_media_group(self, group_id: str, handler: Callable, data: dict):
        # Ждем указанное время для сбора всех сообщений
        await asyncio.sleep(self.latency)

        async with self.lock:
            if group_id not in self.album_data or self.album_data[group_id]["processed"]:
                return

            group_info = self.album_data[group_id]
            messages = group_info["messages"]
            group_info["processed"] = True

            # Удаляем группу из хранилища
            del self.album_data[group_id]

        if messages:
            # Создаем копию data для безопасного использования
            handler_data = data.copy()
            handler_data["album"] = messages

            # Используем последнее сообщение как основное событие
            last_message = messages[-1]

            # Вызываем хендлер
            await handler(last_message, handler_data)