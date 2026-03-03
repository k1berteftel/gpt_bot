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


@admin_router.message(Command('add_link'))
async def add_sponsor_deeplink(msg: Message, session: DataInteraction):
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    sponsors = await session.get_sponsors()
    if msg.from_user.id not in admins:
        sponsor = True
        if msg.from_user.id not in [sponsor.user_id for sponsor in sponsors]:
            return
    else:
        sponsor = False
    arg = msg.text.split(' ')[1]

    if sponsor:
        await session.add_deeplink(arg, arg, msg.from_user.id)
    else:
        await session.add_deeplink(arg, arg)
    await msg.answer('Рекламная ссылка была успешно добавлена')


@admin_router.message(Command('refka'))
async def show_ref_static(msg: Message, session: DataInteraction):
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    sponsors = await session.get_sponsors()
    if msg.from_user.id not in admins:
        divider = True
        if msg.from_user.id not in [sponsor.user_id for sponsor in sponsors]:
            return
    else:
        divider = False
    arg = msg.text.split(' ', maxsplit=1)[1]
    deeplink = await session.get_deeplink_by_name(arg)
    if not deeplink:
        await msg.answer('Такой рекламной ссылки не найдено')
    if divider and deeplink.creator != msg.from_user.id:
        await msg.answer('Такой рекламной ссылки не найдено')
    users = [user for user in await session.get_users() if user.join and user.join == deeplink.link]
    users_len = 0
    refs = 0
    op = 0
    for user in users:
        if not (user.activity - user.entry >= timedelta(minutes=1)):
            continue
        refs += user.refs
        if user.op:
            op += 1
        users_len += 1

    if divider:
        users = int(round(users_len / 1.15)) if users else 0
        refs = int(round(refs / 1.15)) if refs else 0
        op = int(round(op / 1.15)) if op else 0
        gens = int(round(deeplink.gens / 1.15)) if deeplink.gens else 0
    else:
        users = users_len
        gens = deeplink.gens

    text = (f'<b>({deeplink.name}) 🗓 Создано: {datetime.today().strftime("%d-%m-%Y")}</b>\n\n'
            f'Общее:\nВсего: {users}\n - Прошло ОП: {round(op/users*100, 1) if op else 0}%'
            f'\n - Пригласили рефералов: {refs}\n\n\n - Генераций: {gens}'
            f'<b>🔗 Ссылка:</b> <code>https://t.me/gdzavrikbot?start={deeplink.link}</code>')
    await msg.answer(text)


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
