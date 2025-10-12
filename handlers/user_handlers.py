import os

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, StartMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards.keyboard import dialog_keyboard
from utils.wrapper_funcs import generate_wrapper
from utils.ai_funcs import get_text_answer, get_assistant_and_thread, generate_image
from utils.images_funcs import save_bot_files
from database.action_data_class import DataInteraction
from states.state_groups import startSG, DialogSG
from datas.constants import prices
from config_data.config import Config, load_config


user_router = Router()
config: Config = load_config()


@user_router.message(CommandStart())
async def start_dialog(msg: Message, dialog_manager: DialogManager, session: DataInteraction, command: CommandObject, state: FSMContext):
    args = command.args
    referral = None
    link = None
    data = {}
    if args:
        link_ids = await session.get_links()
        ids = [i.link for i in link_ids]
        if args in ids:
            await session.add_admin(msg.from_user.id, msg.from_user.full_name)
            await session.del_link(args)
        if not await session.check_user(msg.from_user.id):
            deeplinks = await session.get_deeplinks()
            deep_list = [i.link for i in deeplinks]
            if args in deep_list:
                link = args
                await session.add_entry(args)
            try:
                args = int(args)
                if not await session.get_op():
                    users = [user.user_id for user in await session.get_users()]
                    if args in users:
                        referral = args
                        await session.add_refs(args)
                        try:
                            await msg.bot.send_message(
                                chat_id=referral,
                                text='<b>+ 10💎 за нового реферала</b>'
                            )
                        except Exception:
                            ...
                else:
                    data['referral'] = args
            except Exception as err:
                print(err)
    await session.add_user(msg.from_user.id, msg.from_user.username if msg.from_user.username else 'Отсутствует',
                           msg.from_user.full_name, referral, link)
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=msg.message_id - 1)
        except Exception:
            ...
        counter = 1
        while dialog_manager.has_context():
            await dialog_manager.done()
            try:
                await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=msg.message_id + counter)
            except Exception:
                ...
            counter += 1
    await dialog_manager.start(state=startSG.start, data=data, mode=StartMode.RESET_STACK)


@user_router.message(DialogSG.waiting_for_message, F.text)
async def process_dialog(msg: Message, session: DataInteraction, dialog_manager: DialogManager,
                         scheduler: AsyncIOScheduler, state: FSMContext):
    try:
        await msg.bot.edit_message_reply_markup(
            chat_id=msg.from_user.id,
            message_id=msg.message_id - 1
        )
    except Exception:
        ...
    state_data = await state.get_data()
    assistant_id, thread_id = state_data.get('assistant_id'), state_data.get('thread_id')
    if not assistant_id or not thread_id:
        assistant_id, thread_id = await get_assistant_and_thread()
        await state.update_data(assistant_id=assistant_id, thread_id=thread_id)
    prompt = msg.text
    answer = await generate_wrapper(
        get_text_answer,
        msg.bot,
        msg.from_user.id,
        prompt, assistant_id, thread_id
    )
    if not answer:
        answer = '❗️Во время операции произошла какая-то ошибка, пожалуйста попробуйте снова'
    await msg.answer(answer, reply_markup=dialog_keyboard)
    """
    task_name = f'{msg.from_user.id}_context'
    for task in asyncio.all_tasks():
        if task.get_name() == task_name:
            task.cancel()
    task = asyncio.create_task(clear_context(state, 60*25))
    task.set_name(task_name)
    """


@user_router.callback_query(F.data == 'back_main')
async def back_main(clb: CallbackQuery, dialog_manager: DialogManager, state: FSMContext):
    await clb.message.delete()
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await clb.bot.delete_message(chat_id=clb.from_user.id, message_id=clb.message.message_id - 1)
        except Exception:
            ...
        counter = 1
        while dialog_manager.has_context():
            await dialog_manager.done()
            try:
                await clb.bot.delete_message(chat_id=clb.from_user.id, message_id=clb.message.message_id + counter)
            except Exception:
                ...
            counter += 1
    await state.clear()
    await dialog_manager.start(state=startSG.start, mode=StartMode.RESET_STACK)


@user_router.callback_query(F.data == 'get_free_crystals')
async def increase_free_value(clb: CallbackQuery, session: DataInteraction, dialog_manager: DialogManager, state: FSMContext):
    await session.update_balance(clb.from_user.id, 10)
    await clb.message.answer('+ 10💎')
    await clb.message.delete()
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await clb.bot.delete_message(chat_id=clb.from_user.id, message_id=clb.message.message_id - 1)
        except Exception:
            ...
        counter = 1
        while dialog_manager.has_context():
            await dialog_manager.done()
            try:
                await clb.bot.delete_message(chat_id=clb.from_user.id, message_id=clb.message.message_id + counter)
            except Exception:
                ...
            counter += 1
    await state.clear()
    await dialog_manager.start(state=startSG.start, mode=StartMode.RESET_STACK)
