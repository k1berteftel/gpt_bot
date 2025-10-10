import uuid
import asyncio
from aiohttp import ClientSession

from aiocryptopay import AioCryptoPay, Networks
from yookassa import Payment, Configuration, Payout
from yookassa.payment import PaymentResponse

from config_data.config import Config, load_config


config: Config = load_config()

crypto_bot = AioCryptoPay(token=config.crypto_bot.token, network=Networks.MAIN_NET)


Configuration.account_id = config.yookassa.account_id
Configuration.secret_key = config.yookassa.secret_key


async def _get_usdt_rub() -> float:
    url = 'https://open.er-api.com/v6/latest/USD'
    async with ClientSession() as session:
        async with session.get(url, ssl=False) as res:
            data = await res.json()
            rub = data['rates']['RUB']
    return float(rub)


async def get_yookassa_url(amount: int, description: str):
    payment = await Payment.create({
        "amount": {
            "value": str(amount) + '.00',
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/Ultragpt_robot"
        },
        "receipt": {
            "customer": {
                "email": "ggasikon@gmail.com"
            },
            'items': [
                {
                    'description': description,
                    "amount": {
                        "value": str(amount) + '.00',
                        "currency": "RUB"
                    },
                    'measure': 'another',
                    'vat_code': 1,
                    'quantity': 1,
                    'payment_subject': 'payment',
                    'payment_mode': 'full_payment'
                }
            ]
        },
        "capture": True,
        "description": description
    }, uuid.uuid4())
    url = payment.confirmation.confirmation_url
    return {
        'url': url,
        'id': payment.id
    }


async def get_crypto_payment_data(amount: int | float):
    usdt_rub = await _get_usdt_rub()
    amount = round(amount / (usdt_rub), 2)
    invoice = await crypto_bot.create_invoice(asset='USDT', amount=amount)
    return {
        'url': invoice.bot_invoice_url,
        'id': invoice.invoice_id
    }


async def check_crypto_payment(invoice_id: int) -> bool:
    invoice = await crypto_bot.get_invoices(invoice_ids=invoice_id)
    if invoice.status == 'paid':
        return True
    return False


async def check_yookassa_payment(payment_id):
    payment: PaymentResponse = await Payment.find_one(payment_id)
    if payment.paid:
        return True
    return False