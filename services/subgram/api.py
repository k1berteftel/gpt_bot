import asyncio
import aiohttp

from config_data.config import Config, load_config

config: Config = load_config()

api_key = config.subgram.api_key

BASE_URL = 'https://api.subgram.ru/'
HEADERS = {
    'Auth': api_key,
    'Content-Type': 'application/json'
}


async def get_user_tasks(user_id: int, premium: bool) -> list[str] | None:
    url = BASE_URL + 'request-op/'
    data = {
        "UserId": str(user_id),
        "ChatId": str(user_id),
        "Premium": premium,
        "MaxOP": 10,
        "action": "newtask",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=HEADERS) as response:
            if response.status not in [200, 201]:
                print(await response.json())
                return None
            data = await response.json()
            if data['code'] != 200:
                print(data['message'])
                return None
            tasks = [task['link'] for task in data['additional']['sponsors'] if task['status'] == 'unsubscribed']
            return tasks


#asyncio.run(get_user_tasks(8005178596, True))


async def check_user_task(user_id: int, task: str) -> bool | None :
    url = BASE_URL + 'get-user-subscriptions'
    data = {
        'user_id': user_id,
        'links': [task]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=HEADERS) as response:
            if response.status not in [200, 201]:
                print(await response.json())
                return None
            data = await response.json()
            if data['code'] != 200:
                print(data['message'])
                return None
            counter = 0
            for task in data['additional']['sponsors']:
                if task['status'] == 'subscribed':
                    return True
            return False


async def check_user_tasks(user_id: int, tasks: list[str]) -> int | None:
    url = BASE_URL + 'get-user-subscriptions'
    data = {
        'user_id': user_id,
        'links': tasks
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=HEADERS) as response:
            if response.status not in [200, 201]:
                print(await response.json())
                return None
            data = await response.json()
            if data['code'] != 200:
                print(data['message'])
                return None
            counter = 0
            for task in data['additional']['sponsors']:
                if task['status'] == 'subscribed':
                    counter += 1
            return counter

