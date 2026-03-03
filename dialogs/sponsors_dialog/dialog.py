from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.sponsors_dialog import getters

from states.state_groups import SponsorsSG


sponsor_dialog = Dialog(
    Window(
        Format('🔗 *Меню управления рекламными ссылками*'),
        Column(
            Select(
                Format('{item[0]}'),
                id='deeplinks_menu_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.deeplink_choose
            ),
        ),
        Row(
            Button(Const('◀️'), id='back_deeplinks_pager', on_click=getters.deeplinks_pager, when='not_first'),
            Button(Format('{page}'), id='deeplinks_pager', when='deeplinks'),
            Button(Const('▶️'), id='next_deeplinks_pager', on_click=getters.deeplinks_pager, when='not_last')
        ),
        SwitchTo(Const('➕ Добавить ссылку'), id='add_link_switcher', state=SponsorsSG.get_link_name),
        Cancel(Const('🔙 Назад'), id='close_admin'),
        getter=getters.links_menu_getter,
        state=SponsorsSG.start
    ),
    Window(
        Const('Введите название для данной ссылки'),
        TextInput(
            id='get_link_name',
            on_success=getters.get_link_name
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=SponsorsSG.start),
        state=SponsorsSG.get_link_name
    ),
    Window(
        Format('{text}'),
        Column(
            Button(Const('🗑Удалить ссылку'), id='del_link', on_click=getters.del_link),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=SponsorsSG.start),
        getter=getters.link_menu_getter,
        state=SponsorsSG.link_menu
    ),
)