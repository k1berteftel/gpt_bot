from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.payment_dialog import getters

from states.state_groups import PaymentSG


payment_dialog = Dialog(
    Window(
        Const('Выберите количество 💎, которые вы хотели бы приобрести'),
        Group(
            Select(
                Format('{item[0]}'),
                id='rate_choose_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.rate_selector
            ),
            width=1
        ),
        Cancel(Const('⬅️Назад'), id='close_dialog'),
        getter=getters.choose_rate_getter,
        state=PaymentSG.choose_rate
    ),
    Window(
        Const('🏦<b>Выберите способ оплаты</b>\n'),
        Format('{text}'),
        Column(
            Button(Const('💳Карта'), id='card_payment_choose', on_click=getters.payment_choose),
            Button(Const('🤖CryptoBot'), id='cb_payment_choose', on_click=getters.payment_choose),
            Button(Const('⭐️Звезды'), id='stars_payment_choose', on_click=getters.payment_choose),
        ),
        SwitchTo(Const('⬅️Назад'), id='back_choose_rate', state=PaymentSG.choose_rate),
        getter=getters.choose_payment_getter,
        state=PaymentSG.choose_payment
    ),
    Window(
        Const('<b>⌛️Ожидание оплаты</b>'),
        Format('{text}'),
        Column(
            Url(Const('🔗Оплатить'), id='url', url=Format('{url}')),
        ),
        Button(Const('⬅️Назад'), id='back_choose_payment', on_click=getters.close_payment),
        getter=getters.process_payment_getter,
        state=PaymentSG.process_payment
    ),
)
