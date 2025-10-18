import os.path

import httpx
import aiohttp
import asyncio
import logging
import uuid
from pathlib import Path

from aiogram import Bot
from aiogram.types import Message
from openai import AsyncOpenAI
from openai.types.beta.threads.message_content_part_param import MessageContentPartParam

from utils.images_funcs import save_image, file_to_url, save_bot_files, download_and_upload_images
from config_data.config import Config, load_config

config: Config = load_config()

proxy = config.proxy

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=config.openai.token,
    http_client=httpx.AsyncClient(proxies=f'http://{proxy.login}:{proxy.password}@{proxy.ip}:{proxy.port}')
)


async def solve_task(image: str, prompt: str | None = None):
    images = [{'type': 'image_url', "image_url": {"url": image}}]
    system_prompt = ("Реши задачу и представь решение в понятном, читаемом формате без "
                     "использования LaTeX и боксов. Используй обычные математические "
                     "символы и простым языком, пошагово объясняй каждое свое "
                     "действие в решении данной тебе задачи. Сами математические действия "
                     "возвращай строго в формате <code>действие</code>")
    prompt = system_prompt if not prompt else system_prompt + (f'\nВот пользовательский промпт к '
                                                               f'решению задачи: "{prompt}"')
    response = await client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *images
                ]
            }
        ],
    )
    print(response.usage.total_tokens, response.usage.prompt_tokens, response.usage.completion_tokens)
    print(response.choices[0].message.content)
    return response.choices[0].message.content


async def get_prompt_answer(prompt: str, text: str, image: str | None = None) -> str:
    messages = []
    messages.append({'role': 'system', 'content': prompt})
    if image:
        messages.append({'type': 'image_url', "image_url": {"url": image}})
    messages.append({"role": "user", "content": text})
    response = await client.chat.completions.create(
        model='gpt-4.1-mini',
        messages=messages
    )
    return response.choices[0].message.content.strip()


async def get_assistant_and_thread(model: str = 'gpt-4.1-mini', role: str | None = None):
    """
    :param model: модель чата гпт
    :return: Две str переменной по факту являющиеся уникальными для каждого юзера, чтобы обрабатывать их
        диалог отдельно от других юзеров
    """
    assistant = await client.beta.assistants.create(
        model=model,
        instructions=role,
        temperature=1.0,
        name="Яна"
    )

    thread = await client.beta.threads.create()
    return assistant.id, thread.id


#print(asyncio.run(get_assistant_and_thread()))


async def get_text_answer(prompt: str, assistant_id: str, thread_id: str, images: list[str] = None) -> str | dict | None:
    """
        Обработка ИИшкой сообщения юзера, возвращает ответ ИИ
    """
    images = [{'type': 'image_url', "image_url": {"url": photo}} for photo in images]
    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    if images:
        content.extend(images)
    message = await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )
    print(message.__dict__)
    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    logger.info(run.status)
    logger.info(run.last_error)
    info = (f'Стоимость запроса: {run.usage.completion_tokens}\nСтоимость промпта: {run.usage.prompt_tokens}'
            f'\nОбщая стоимость: {run.usage.total_tokens}')
    logger.info(info)
    if run.status == "completed":
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        logger.info(messages)

        async for message in messages:
            logger.info(message.content[0].text.value)
            return message.content[0].text.value


async def generate_on_api(params: dict) -> str:
    url = 'http://127.0.0.1:8000/'
    async with aiohttp.ClientSession() as session:
        async with session.post(url + 'generate', json=params, ssl=False) as response:
            if response.status != 200:
                raise RuntimeError(f"Ошибка сети при обращении к API: {await response.content.read()}")
            data = await response.json()
            task_id = data['task_id']
        url = f'http://127.0.0.1:8000/result/{task_id}'
        while True:
            async with session.get(url) as response:
                if response.status != 200:
                    raise RuntimeError(f"Ошибка сети при обращении к API: {await response.content.read()}")
                data = await response.json()
                if data['status'] == 'failed':
                    raise Exception(data['message'])
                if data['status'] == 'completed':
                    return data['result']
            await asyncio.sleep(4)


counter = 1


async def generate_division(prompt: str, bot: Bot, photos: list[Message] | None = None) -> str | dict:
    global counter
    images = []
    #if counter % 2 == 0:
    if photos:
        images = await download_and_upload_images(bot, photos)
    result = await generate_image_by_unifically(prompt, images)
    if isinstance(result, dict):
        if photos:
            images = await save_bot_files(photos, bot)
        result = await generate_image_by_veo(prompt, images)
        for image in images:
            if os.path.exists(image):
                os.remove(image)
    return result
"""
    else:
        if photos:
            images = await save_bot_files(photos, bot)
        result = await generate_image_by_veo(prompt, images)
        for image in images:
            if os.path.exists(image):
                os.remove(image)
        if isinstance(result, dict):
            if photos:
                images = await download_and_upload_images(bot, photos)
            result = await generate_image_by_unifically(prompt, images)
    counter += 1
    return result
"""


async def _polling_unifically_generate(data: dict) -> list[str] | dict:
    url = f'https://api.unifically.com/nano-banana/status/{data["data"]["task_id"]}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    async with aiohttp.ClientSession() as client:
        while True:
            async with client.get(url, headers=headers, ssl=False) as response:
                if response.status not in [200, 201]:
                    data = await response.json()
                    return {'error': data['data']['error']['message']}
                data = await response.json()
                print(data)
            if data['data']['status'] == 'failed':
                return {'error': data['data']['error']['message']}
            if data['data']['status'] == 'completed':
                return [data['data']['output']['image_url']]
            await asyncio.sleep(4)


async def generate_image_by_unifically(prompt: str, photos: list[str]) -> list[str] | dict:
    url = f'https://api.unifically.com/nano-banana/generate'
    #prompt = await translate_text(prompt)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    data = {
      "prompt": prompt,
    }
    if photos:
        data["image_urls"] = photos
    async with aiohttp.ClientSession() as client:
        async with client.post(url, headers=headers, json=data, ssl=False) as response:
            print(response.status)
            if response.status not in [200, 201]:
                data = await response.json()
                return {'error': data['data']['error']['message']}
            data = await response.json()
            print(data)
        if data['code'] != 200:
            return {'error': data['data']['error']['message']}
        if data['data'].get('output'):
            return [data['data']['output']['image_url']]
    return await _polling_unifically_generate(data)


async def _polling_veo_generate(req_id: str) -> list[str] | dict:
    url = f'http://95.164.55.41:8765/v1/gemini/image-status/{req_id}'
    headers = {'Authorization': f'Bearer {config.veo.api_key}'}
    logger.info('Start image generate polling')
    async with aiohttp.ClientSession() as session:
        counter = 1
        while True:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status not in [200, 201]:
                    return {'error': f"Request status code {response.status}"}
                data = await response.json()
                status = data.get('status')
                if status and status == 'failed':
                    return {'error': data['error']}
                if not status and data['success']:
                    image_data = data['images'][0]
                    try:
                        file_path = await save_image(image_data)
                    except Exception as e:
                        return {'error': str(e)}
                    file_url = await file_to_url(file_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    if not file_url:
                        return {'error': "ImgBB error"}
                    return [file_url]
            logger.info(f'Polling retry: {counter}')
            counter += 1
            await asyncio.sleep(3)


async def generate_image_by_veo(prompt: str, photos: list[str] = None) -> list[str] | dict:
    url = "http://95.164.55.41:8765/v1/gemini/generate-image-async"
    data = aiohttp.FormData()
    data.add_field('prompt', prompt)

    opened_files = []
    if photos:
        for image_path in photos:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Файл {image_path} не найден")

            file_obj = open(image_path, 'rb')
            opened_files.append(file_obj)

            ext = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.webp': 'image/webp', '.bmp': 'image/bmp',
                '.tiff': 'image/tiff', '.tif': 'image/tiff'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

            data.add_field(
                'reference_images',
                file_obj.read(),
                filename=Path(image_path).name,
                content_type=mime_type
            )
    for file in opened_files:
        file.close()

    headers = {'Authorization': f'Bearer {config.veo.api_key}'}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers, ssl=False) as response:
            if response.status not in [200, 201]:
                print(response.status)
                return {'error': f"Request status code {response.status}"}
            data = await response.json()
            logger.info('Success input data load')
            if data['status'] != 'queued':
                return {'error': data['message']}
            req_id = data['request_id']
            logger.info('Success request_id save')
    return await _polling_veo_generate(req_id)

#"""
