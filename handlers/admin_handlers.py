from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram_dialog import DialogManager, StartMode

from config_data.config import load_config, Config
from database.action_data_class import DataInteraction
from states.state_groups import startSG


config: Config = load_config()

admin_router = Router()


@admin_router.message(Command('add_sponsor'))
async def handle_add_sponsor(msg: Message, session: DataInteraction):
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    if msg.from_user.id not in admins:
        return
    arg = msg.text.split(' ')[1]
    try:
        user_id = int(arg)
    except Exception:
        await msg.answer('Telegram ID спонсора должно быть числом')
        return
    sponsors = await session.get_sponsors()
    if user_id in [sponsor.user_id for sponsor in sponsors]:
        await msg.answer('Такой спонсор уже существует')
        return
    await session.add_sponsor(user_id)
    await msg.answer('Спонсор был успешно добавлен')


@admin_router.message(Command('refs'))
async def send_sponsor_static(msg: Message, session: DataInteraction):
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    sponsors = await session.get_sponsors()
    if msg.from_user.id not in admins:
        sponsor = True
        if msg.from_user.id not in [sponsor.user_id for sponsor in sponsors]:
            return
    else:
        sponsor = False

    if sponsor:
        deeplinks = [deeplink for deeplink in await session.get_deeplinks() if deeplink.creator and deeplink.creator == msg.from_user.id]
    else:
        deeplinks = list(await session.get_deeplinks())

    text = 'Ваши ссылки:\n'

    counter = 1
    users = 0
    for link in deeplinks:
        link_users = 0
        for user in [user for user in await session.get_users() if user.join and user.join == link.link]:
            if not (user.activity - user.entry >= timedelta(minutes=1)):
                continue
            link_users += 1
        link_users = int(round(link_users / 1.15)) if link_users else 0
        text += f'{counter}. {link.name} - {link_users}\n'
        users += link_users
        counter += 1
    text += f'\n<b>Всего: </b> {users}'
    await msg.answer(text)
