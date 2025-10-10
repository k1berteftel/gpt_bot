import datetime
import random
from typing import Literal
import asyncio
from asyncio import TimeoutError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from nats.js import JetStreamContext

from utils.payments.create_payment import check_yookassa_payment, check_crypto_payment
from database.action_data_class import DataInteraction
from config_data.config import Config, load_config


config: Config = load_config()


async def wait_for_payment(
        payment_id,
        user_id: int,
        bot: Bot,
        session: DataInteraction,
        amount: int,
        payment_type: Literal['card', 'cryptoBot'],
        timeout: int = 60 * 15,
        check_interval: int = 6
):
    """
    Ожидает оплаты в фоне. Завершается при оплате или по таймауту.
    """
    try:
        await asyncio.wait_for(_poll_payment(payment_id, user_id, amount, bot, session, payment_type, check_interval),
                                             timeout=timeout)

    except TimeoutError:
        print(f"Платёж {payment_id} истёк (таймаут)")

    except Exception as e:
        print(f"Ошибка в фоновом ожидании платежа {payment_id}: {e}")


async def _poll_payment(payment_id, user_id: int, amount: int, bot: Bot, session: DataInteraction, payment_type: str, interval: int):
    """
    Цикл опроса статуса платежа.
    Завершается, когда платёж оплачен.
    """
    while True:
        if payment_type == 'card':
            status = await check_yookassa_payment(payment_id)
        else:
            status = await check_crypto_payment(payment_id)
        if status:
            await bot.send_message(
                chat_id=user_id,
                text='✅Оплата прошла успешно'
            )
            await execute_rate(user_id, bot, amount, session)
            break
        await asyncio.sleep(interval)


async def execute_rate(user_id: int, bot: Bot, amount: int,
                       session: DataInteraction):
    await session.update_balance(user_id, amount)
    user = await session.get_user(user_id)
    await session.add_income(amount)
    if user.join:
        await session.update_deeplink_earn(user.join, amount)
    if user.referral:
        earn = int(amount * 0.1)
        await session.update_user_earn(user.referral, earn)
    try:
        await bot.send_message(
            chat_id=user_id,
            text='✅<b>Ваш баланс был успешно пополнен</b>, чтобы вернуться в главное меню введите команду /start'
        )
    except Exception:
        ...

