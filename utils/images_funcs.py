import asyncio
import os
import base64
import logging
from pathlib import Path

import aiohttp
import aiofiles

from aiogram import Bot
from aiogram.types import PhotoSize, Message

from utils.build_ids import get_random_id
from config_data.config import Config, load_config

config: Config = load_config()


async def _upload_image_to_imgbb(image_path: str) -> str | None:
    url = 'https://files.storagecdn.online/upload'

    data = aiohttp.FormData()
    data.add_field('file',
                   open(image_path, 'rb'),
                   filename=Path(image_path).name,
                   content_type='application/octet-stream')

    headers = {
        'Authorization': f'Bearer {config.unifically.api_token}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.put(url, data=data, headers=headers, ssl=False) as response:
            if response.status not in [200, 201]:
                print(await response.text())
                return None
            data = await response.json()
            if data['success'] != True:
                print(data['message'])
                return None
    return data['file_url']


async def image_to_url(photo: PhotoSize, bot: Bot) -> str:
    if not os.path.exists('download'):
        os.mkdir('download')
    temp_photo_path = f"download/temp_{photo.file_unique_id}.jpg"

    try:
        await bot.download(file=photo.file_id, destination=temp_photo_path)

        image_url = await _upload_image_to_imgbb(temp_photo_path)
        if image_url:
            return image_url
        else:
            logging.warning(f"Не удалось загрузить на ImgBB файл: {temp_photo_path}")

    finally:
        if os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)


async def save_bot_files(msgs: list[Message], bot: Bot):
    if not os.path.exists('download'):
        os.mkdir('download')
    files = []
    for msg in msgs:
        photo = msg.photo[-1]
        temp_photo_path = f"download/temp_{photo.file_unique_id}.jpg"
        try:
            await bot.download(file=photo.file_id, destination=temp_photo_path)

            files.append(temp_photo_path)
        except Exception as err:
            logging.warning(f"Не удалось загрузить на ImgBB файл: {temp_photo_path}\n{err}")
    return files


async def file_to_url(file_path: str):
    return await _upload_image_to_imgbb(file_path)


async def save_image(data: dict) -> str:
    """
    Сохраняет base64 изображение в файл
    :param data: словарь с данными изображения
    """
    try:
        filename = get_random_id()
        base64_data = data.get("data", "")
        mime_type = data.get("mime_type", "image/png")

        if not base64_data:
            raise ValueError("Нет данных изображения")

        image_bytes = base64.b64decode(base64_data)

        extension = mime_type.split('/')[-1]
        if extension == "jpeg":
            extension = "jpg"

        if not filename.endswith(f".{extension}"):
            filename = f"download/{Path(filename).stem}.{extension}"

        async with aiofiles.open(filename, 'wb') as file:
            await file.write(image_bytes)

        return filename

    except Exception as e:
        print(f"❌ Ошибка при сохранении изображения: {e}")
        raise e