from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.user_dialog import getters

from states.state_groups import startSG, adminSG, PaymentSG, SponsorsSG

user_dialog = Dialog(
    Window(
        DynamicMedia('media'),
        Format('{text}'),
        Button(Const('💬GPT чат'), id='gpt_chat_switcher', on_click=getters.gpt_switcher),
        Row(
            SwitchTo(Const('🏞Изображение'), id='image_menu_switcher', state=startSG.image_menu),
            SwitchTo(Const('🎞Видео'), id='video_menu_switcher', state=startSG.video_menu)
        ),
        Column(
            SwitchTo(Const('👨‍🏫Cтудентам и школьникам'), id='students_menu_switcher', state=startSG.students_menu),
            SwitchTo(Const('👤Профиль'), id='profile_switcher', state=startSG.profile),
            #SwitchTo(Const('🎁Задания'), id='tasks_menu_swithcer', state=startSG.tasks_menu),
            Start(Const('💰Пополнить баланс'), id='payment_menu', state=PaymentSG.choose_rate),
            Start(Const('Админ панель'), id='admin', state=adminSG.start, when='admin'),
            Start(Const('Партнерские ссылки'), id='sponsors', state=SponsorsSG.start, when='sponsors'),
        ),
        getter=getters.start_getter,
        state=startSG.start
    ),
    Window(
        Const('🎒Тут собранны все нейронные сети помогут вам во время учебы'),
        Column(
            Button(Const('📸Решальник задач'), id='task_photo_switcher', on_click=getters.balance_check_switcher),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        state=startSG.students_menu
    ),
    Window(
        Const('Отправьте фото задачи, которую вы хотите решить⬇️'),
        MessageInput(
            func=getters.get_task_prompt,
            content_types=ContentType.PHOTO
        ),
        MessageInput(
            func=getters.get_task_wrong,
            content_types=ContentType.ANY
        ),
        SwitchTo(Const('⬅️Назад'), id='back_students_menu', state=startSG.students_menu),
        state=startSG.get_task_photo
    ),
    Window(
        Format('{text}'),
        Column(
            Button(Format('Только текст'), id='text_image_choose', on_click=getters.image_choose),
            Button(Format('Текст + фото'), id='combo_image_choose', on_click=getters.image_choose),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.image_menu_getter,
        state=startSG.image_menu
    ),
    Window(
        Const('📝 Отправьте промпт для генерации изображения\n'),
        Format('<b>💡Подсказка: {hint}</b>\n'),
        Format('Стоимость: <b>{cost}</b> 💎'),
        TextInput(
            id='get_image_text',
            on_success=getters.get_image_text
        ),
        MessageInput(
            func=getters.get_image_prompt,
            content_types=ContentType.PHOTO
        ),
        MessageInput(
            func=getters.get_image_wrong,
            content_types=ContentType.ANY
        ),
        #Button(Const('💡Сгенерировать промпт'), id='image_gen_prompt_switcher', on_click=getters.gen_prompt_switcher),
        SwitchTo(Const('⬅️Назад'), id='back_image_menu', state=startSG.image_menu),
        getter=getters.get_image_prompt_getter,
        state=startSG.get_image_prompt
    ),
    Window(
        Const('Выберите модель для генерации видео:'),
        Column(
            Button(Const('Kling v2.1'), id='kling_video_choose', on_click=getters.video_choose),
            Button(Const('Seedance 1'), id='seedance_video_choose', on_click=getters.video_choose),
            Button(Const('Sora 2'), id='sora_video_choose', on_click=getters.video_choose),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        state=startSG.video_menu
    ),
    Window(
        Format('{text}'),
        Group(
            Select(
                Format('{item[0]}'),
                id='sub_model_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.sub_model_choose
            ),
            width=1
        ),
        SwitchTo(Const('⬅️Назад'), id='back_video_menu', state=startSG.video_menu),
        getter=getters.video_model_getter,
        state=startSG.video_model_menu
    ),
    Window(
        Const('📝Отправьте промпт для генерации видео\n'),
        Format('<b>💡Подсказка:</b> {hint}\n'),
        Format('{params}'),
        TextInput(
            id='get_video_text',
            on_success=getters.get_video_text
        ),
        MessageInput(
            func=getters.get_video_prompt,
            content_types=ContentType.PHOTO
        ),
        MessageInput(
            func=getters.get_video_wrong,
            content_types=ContentType.ANY
        ),
        Row(
            SwitchTo(Const('🕝Длительность'), id='time_choose_switcher', state=startSG.time_choose, when='is_param'),
            SwitchTo(Const('📐Соотношение сторон'), id='ratio_choose_switcher', state=startSG.ratio_choose, when='is_param'),
        ),
        #Button(Const('💡Сгенерировать промпт'), id='video_gen_prompt_switcher', on_click=getters.gen_prompt_switcher),
        SwitchTo(Const('⬅️Назад'), id='back_video_menu', state=startSG.video_menu),
        getter=getters.get_video_prompt_getter,
        state=startSG.get_video_prompt
    ),
    Window(
        Const('⌛️Выберите длительность видеоряда:'),
        Group(
            Select(
                Format('{item[0]}'),
                id='time_choose_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.time_selector
            ),
            width=1
        ),
        SwitchTo(Const('⬅️Назад'), id='back_get_video_prompt', state=startSG.get_video_prompt),
        getter=getters.time_choose_getter,
        state=startSG.time_choose
    ),
    Window(
        Const('📐Выберите соотношение сторон для вашего видеоряда:'),
        Group(
            Select(
                Format('{item[0]}'),
                id='ratio_choose_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.ratio_selector
            ),
            width=1
        ),
        SwitchTo(Const('⬅️Назад'), id='back_get_video_prompt', state=startSG.get_video_prompt),
        getter=getters.ratio_choose_getter,
        state=startSG.ratio_choose
    ),
    Window(
        Format('{text}'),
        TextInput(
            id='get_gen_prompt_text',
            on_success=getters.get_gen_prompt_text
        ),
        MessageInput(
            func=getters.get_gen_prompt_message,
            content_types=ContentType.PHOTO
        ),
        Button(Const('⬅️Назад'), id='back_to_generate', on_click=getters.generate_switcher),
        getter=getters.gen_prompt_menu_getter,
        state=startSG.gen_prompt_menu
    ),
    Window(
        DynamicMedia('media'),
        Format('{text}'),
        Column(
            Url(Const('✈️Поделиться'), id='share_url', url=Format('{url}')),
            Start(Const('💰Пополнить баланс'), id='payment_menu', state=PaymentSG.choose_rate),
            Url(Const('ℹ️Помощь'), id='help_url', url=Const('https://t.me/ultragptsupport_bot')),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.profile_getter,
        state=startSG.profile
    ),
    Window(
        DynamicMedia('media'),
        Format('{text}\n'),
        Format('Стоимость: {cost} 💎'),
        Column(
            Button(Const('😃Начать генерацию'), id='start_generate_switcher', on_click=getters.balance_check_switcher),
            Url(Const('💡Идея для генерации'), id='exemple_url', url=Format('{url}'))
        ),
        Button(Const('⬅️Назад'), id='back_choose_model', on_click=getters.back_choose_model),
        getter=getters.example_menu_getter,
        state=startSG.example_menu
    ),
    Window(
        Format('<b>❌ Не хватает алмазов!</b>\n💸 Ваш баланс: {balance} 💎\n\n<b>Для генерации нужно:</b>'
               '\nСтоимость: {price} 💎\n\n<b>Как быстро получить алмазы?</b>\n<blockquote><b>🎁 Пригласите друзей</b>\n'
               'Получите <b>10 💎 за каждого</b> приглашенного друга + 10% от его пополнений!\n'
               '\n\n💎 <b>Или пополните баланс</b>\nМгновенно получите нужную сумму и '
               'продолжайте творить</blockquote>\n\n👇 Выберите способ:'),
        Column(
            Url(Const('🎁 Пригласить друзей'), id='follow_url', url=Format('{url}')),
            #SwitchTo(Const('💎Бесплатные'), id='task_menu_switcher', state=startSG.tasks_menu),
            Start(Const('💰Пополнить баланс'), id='payment_menu', state=PaymentSG.choose_rate),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.enough_balance_getter,
        state=startSG.enough_balance
    ),
    Window(
        Const('🎁Выполняйте задания и получайте бесплатные 💎'),
        Format('{text}'),
        Column(
            Url(Format('Получить {amount}💎'), id='task_url', url=Format('{url}'), when='tasks'),
            Button(Const('✔️Проверить выполнение'), id='check_task', on_click=getters.check_task, when='tasks'),
        ),
        Row(
            Button(Const('◀️'), id='back_tasks_pager', on_click=getters.tasks_pager, when='not_first'),
            Button(Format('{page}'), id='tasks_pager', when='tasks'),
            Button(Const('▶️'), id='next_tasks_pager', on_click=getters.tasks_pager, when='not_last')
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.tasks_menu_getter,
        state=startSG.tasks_menu
    ),
)