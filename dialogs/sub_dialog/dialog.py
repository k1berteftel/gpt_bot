from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Url, ListGroup
from aiogram_dialog.widgets.text import Format, Const

from dialogs.sub_dialog import getters
from states.state_groups import SubSG


sub_dialog = Dialog(
    Window(
        Format('{text}'),
        Column(
            ListGroup(
                Url(Format('{item[0]}'), url=Format('{item[1]}')),
                id='sub_builder',
                items='items',
                item_id_getter=lambda x: x[2]
            ),
        ),
        Button(Format('{check_sub}'), id='check_sub', on_click=getters.check_sub),
        getter=getters.sub_getter,
        state=SubSG.start
    )
)