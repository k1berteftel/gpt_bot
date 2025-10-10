from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, StartMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.payments.process_payment import execute_rate
from config_data.config import Config, load_config
from database.action_data_class import DataInteraction
from states.state_groups import startSG


config: Config = load_config()
payment_router = Router()


@payment_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def success_payment(msg: Message, session: DataInteraction, state: FSMContext, dialog_manager: DialogManager):
    amount = int(msg.successful_payment.invoice_payload)
    await msg.delete()
    await execute_rate(msg.from_user.id, msg.bot, amount, session)
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
    await dialog_manager.start(startSG.start, mode=StartMode.RESET_STACK)


@payment_router.callback_query(F.data == 'close_payment')
async def close_payment(clb: CallbackQuery, dialog_manager: DialogManager):
    try:
        await clb.message.delete()
    except Exception:
        ...