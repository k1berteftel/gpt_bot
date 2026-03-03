import os
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput

from utils.build_ids import get_random_id
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import SponsorsSG


async def links_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    buttons = dialog_manager.dialog_data.get('deeplinks')
    if not buttons:
        links = [deeplink for deeplink in await session.get_deeplinks() if deeplink.creator and deeplink.creator == event_from_user.id]
        buttons = [(f'{link.name} ({link.entry})', link.id) for link in links]
        buttons = [buttons[i:i + 10] for i in range(0, len(buttons), 10)]
        dialog_manager.dialog_data['deeplinks'] = buttons
    page = dialog_manager.dialog_data.get('page')
    if not page:
        page = 0
        dialog_manager.dialog_data['page'] = page
    not_first = False
    not_last = False
    if page != 0:
        not_first = True
    if len(buttons) and page != len(buttons) - 1:
        not_last = True
    print(buttons)
    return {
        'items': buttons[page] if buttons else [],
        'page': f'{page + 1}/{len(buttons)}',
        'not_first': not_first,
        'not_last': not_last
    }


async def deeplinks_pager(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    page = dialog_manager.dialog_data.get('page')
    action = clb.data.split('_')[0]
    if action == 'back':
        page -= 1
    else:
        page += 1
    dialog_manager.dialog_data['page'] = page
    await dialog_manager.switch_to(SponsorsSG.start)


async def get_link_name(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.add_deeplink(text, text)
    links = [deeplink for deeplink in await session.get_deeplinks() if deeplink.creator and deeplink.creator == msg.from_user.id]
    buttons = [(f'{link.name} ({link.entry})', link.id) for link in links]
    buttons = [buttons[i:i + 10] for i in range(0, len(buttons), 10)]
    print(buttons)
    dialog_manager.dialog_data['deeplinks'] = buttons
    await dialog_manager.switch_to(SponsorsSG.start)


async def deeplink_choose(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['deeplink_id'] = int(item_id)
    await dialog_manager.switch_to(SponsorsSG.link_menu)


async def link_menu_getter(dialog_manager: DialogManager, **kwargs):
    deeplink_id = dialog_manager.dialog_data.get('deeplink_id')
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    deeplink = await session.get_deeplink(deeplink_id)
    users = [user for user in await session.get_users() if user.join and user.join == deeplink.link]
    users_len = 0
    refs = 0
    op = 0
    gens = 0
    for user in users:
        if not (user.activity - user.entry >= timedelta(minutes=1)):
            continue
        refs += user.refs
        if user.op:
            op += 1
        users_len += 1
        gens += user.gens

    users = int(round(users_len / 1.15)) if users else 0
    refs = int(round(refs / 1.15)) if refs else 0
    op = int(round(op / 1.15)) if op else 0
    gens = int(round(gens / 1.15)) if gens else 0

    text = (f'<b>({deeplink.name}) 🗓 Создано: {datetime.today().strftime("%d-%m-%Y")}</b>\n\n'
            f'Общее:\nВсего: {users}\n - Прошло ОП: {round(op/users*100, 1) if op else 0}%'
            f'\n - Пригласили рефералов: {refs}\n\n\n - Генераций: {gens}'
            f'<b>🔗 Ссылка:</b> <code>https://t.me/Ultragpt_robot?start={deeplink.link}</code>')
    return {'text': text}


async def del_link(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    deeplink_id = dialog_manager.dialog_data.get('deeplink_id')
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_deeplink(deeplink_id)

    await clb.answer('Данный диплинк был успешно удален')

    links = [deeplink for deeplink in await session.get_deeplinks() if deeplink.creator and deeplink.creator == clb.from_user.id]
    buttons = [(f'{link.name} ({link.entry})', link.id) for link in links]
    buttons = [buttons[i:i + 10] for i in range(0, len(buttons), 10)]
    dialog_manager.dialog_data['deeplinks'] = buttons
    dialog_manager.dialog_data['page'] = 0
    dialog_manager.dialog_data['deeplink_id'] = None
    await dialog_manager.switch_to(SponsorsSG.start)