import datetime
import os

from aiogram.types import CallbackQuery, User, Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput

from services.subgram.api import get_user_tasks, check_user_tasks, check_user_task
from utils.images_funcs import image_to_url, save_bot_files
from utils.ai_funcs import get_prompt_answer, generate_division, generate_on_api, solve_task
from utils.wrapper_funcs import generate_wrapper
from keyboards.keyboard import dialog_keyboard
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from datas.constants import prices, get_video_price, duration_prices, model_ratios, model_examples
from states.state_groups import startSG, DialogSG, PaymentSG


config: Config = load_config()


async def start_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    admin = False
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    if event_from_user.id in admins:
        admin = True
    free = True
    if not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1):
        free = True
    sponsor = False
    if event_from_user.id in [user.user_id for user in await session.get_sponsors()]:
        sponsor = True
    bonus_text = "\n🎁<b>Бонус</b>: Каждый день тебе доступна <b>1 бесплатная генерация с текстом!</b>" if free else ""
    text = (f'<b>Добро пожаловать в Ultra GPT 👋🏻 </b>\n\n'
            f'<b>💬 Умный диалог</b> — Задавай вопросы, ищи идеи или просто общайся с продвинутым ИИ.\n'
            f'<b>🎨 Генерация изображений</b> — Опиши картинку словами — и я её нарисую.\n'
            f'<b>🎬 Создание видео</b>. — Преврати свою идею в короткое и яркое видео.'
            f'\n\n<b>Твой баланс:</b> {user.balance}💎'
            f' {bonus_text}')
    media = MediaAttachment(type=ContentType.PHOTO, path='media/menu.jpg')
    return {
        'sponsors': sponsor,
        'media': media,
        'text': text,
        'admin': admin
    }


async def gpt_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    print(dialog_manager.middleware_data.get('state'), dialog_manager.middleware_data.get('context'))
    state: FSMContext = dialog_manager.middleware_data.get('state')
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
    await state.set_state(DialogSG.waiting_for_message)
    await clb.message.answer('Что бы вы хотели узнать на этот раз?', reply_markup=dialog_keyboard)


async def get_task_wrong(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    await msg.delete()
    await msg.answer('❗️Отправьте пожалуйста фото задачи')


async def get_task_prompt(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(msg.from_user.id)
    price = prices['task']
    if user.balance < price:
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    prompt = msg.caption
    image = await image_to_url(msg.photo[-1], msg.bot)
    result = await generate_wrapper(
        solve_task,
        msg.bot,
        msg.from_user.id,
        image, prompt
    )
    if not result:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        return
    message = await msg.answer_photo(
        photo=result
    )
    await session.update_balance(msg.from_user.id, -price)
    await session.update_gens(msg.from_user.id)
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.get_task_photo)


async def gen_prompt_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['gen'] = clb.data.split('_')[0]
    await dialog_manager.switch_to(startSG.gen_prompt_menu)


async def gen_prompt_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    gen = dialog_manager.dialog_data.get('gen')
    model = dialog_manager.dialog_data.get('model')
    if gen == 'image':
        if model == 'text':
            text = ('👇Опишите какую картинку вы хотели бы сгенерировать, а я помогу вам подобрать '
                    'правильный промпт для этой генерации')
        else:
            text = ('👇Отправьте фото и его изменения текстом, которые вы хотели бы произвести с этим фото, '
                    'а я помогу вам подобрать правильный промпт для этой генерации')
    else:
        if model == 'seedance':
            text = ('👇Опишите сценарий видео, которое вы хотели бы сгенерировать, а я помогу вам подобрать '
                    'правильный промпт для этой генерации')
        else:
            text = ('👇Отправьте фото и текстый сценарий видео для прикрепленного фото, а я помогу вам '
                    'подобрать правильный промпт для этой генерации')
    return {
        'text': text
    }


async def get_gen_prompt_text(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    gen = dialog_manager.dialog_data.get('gen')
    model = dialog_manager.dialog_data.get('model')
    if gen == 'image':
        if model == 'combo':
            await msg.delete()
            await msg.answer('❗️Отправьте пожалуйста фото и текст изменений к нему')
            return
    else:
        if model == 'kling':
            await msg.delete()
            await msg.answer('❗️Отправьте пожалуйста фото и текст сценария видео к прикрепленному фото')
    if gen == 'image':
        prompt = ('Твоя задача помочь пользователю создать компактный и подробный промпт для генерации фото под его запрос\n'
                  '!!В ответ отправляй только сгенерированный тобою промпт')
    else:
        prompt = ('Твоя задача помочь пользователю создать компактный и подробный промпт для генерации видео под его запрос\n'
                  '!!В ответ отправляй только сгенерированный тобою промпт')
    answer = await generate_wrapper(
        get_prompt_answer,
        msg.bot,
        msg.from_user.id,
        prompt, text
    )
    if not answer:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        return
    if isinstance(answer, dict):
        await msg.answer(f'🚨Во время генерации произошла ошибка:\n<code>{answer.get("error")}</code>')
        return
    await msg.answer(f'Вот ваш промпт для генерации:\n\n<code>{answer}</code>')
    if gen == 'image':
        await dialog_manager.switch_to(startSG.get_image_prompt)
    else:
        await dialog_manager.switch_to(startSG.get_video_prompt)


async def get_gen_prompt_message(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    gen = dialog_manager.dialog_data.get('gen')
    model = dialog_manager.dialog_data.get('model')
    if gen == 'image':
        if model == 'text':
            await msg.delete()
            await msg.answer('❗️Отправьте пожалуйста только текстовый промпт')
            return
    else:
        if model == 'seedance':
            await msg.delete()
            await msg.answer('❗️Отправьте пожалуйста только текстовый промпт к сценарию видео')

    if gen == 'image':
        prompt = ('Твоя задача помочь пользователю создать компактный и подробный промпт для генерации фото под его запрос\n'
                  '!!В ответ отправляй только сгенерированный тобою промпт')
    else:
        prompt = ('Твоя задача помочь пользователю создать компактный и подробный промпт для генерации видео под его запрос\n'
                  '!!В ответ отправляй только сгенерированный тобою промпт')
    image = await image_to_url(msg.photo[-1], msg.bot)
    text = msg.caption
    answer = await generate_wrapper(
        get_prompt_answer,
        msg.bot,
        msg.from_user.id,
        prompt, text, image
    )
    if not answer:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        return
    if isinstance(answer, dict):
        await msg.answer(f'🚨Во время генерации произошла ошибка:\n<code>{answer.get("error")}</code>')
        return
    if gen == 'image':
        await dialog_manager.switch_to(startSG.get_image_prompt)
    else:
        await dialog_manager.switch_to(startSG.get_video_prompt)
    await msg.answer(f'Вот ваш промпт для генерации:\n\n<code>{answer}</code>')


async def generate_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    gen = dialog_manager.dialog_data.get('gen')
    dialog_manager.dialog_data['gen'] = None
    if gen == 'image':
        await dialog_manager.switch_to(startSG.get_image_prompt)
    else:
        await dialog_manager.switch_to(startSG.get_video_prompt)


async def image_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data['mode'] = 'image'
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    free = False
    if not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1):
        free = True
    text = (f'Выберите какую генерацию вы хотели бы сделать:\n\n📝<b>"Только текст"</b> ({prices["image"]["text"]} 💎) '
            f'- это когда ты пишешь только'
            f' текстовый промпт, а ИИ сам «придумывает» и рисует такую картинку\n\n🖼<b>"Текст + фото"</b> '
            f'({prices["image"]["combo"]} 💎) - ИИ '
            f'использует твою фотографию как образец — он сохраняет стиль, позу, цвета, но уже с новым '
            f'содержанием по твоему описанию.\n\n')
    if free:
        text = '🎁<b> Вам доступна 1 бесплатная генерация с текстом в сутки.</b> \n\n' + text
    return {
        'text': text
    }


async def image_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    model = clb.data.split('_')[0]
    dialog_manager.dialog_data['model'] = model
    """
    mode = dialog_manager.dialog_data.get('mode')
    price = prices[mode][model]
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(clb.from_user.id)
    free = False
    if model == 'text' and (not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1)):
        free = True
    if not free and user.balance < price:
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    """
    await dialog_manager.switch_to(startSG.example_menu)


async def get_image_prompt_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    model = dialog_manager.dialog_data.get('model')
    mode = dialog_manager.dialog_data.get('mode')
    price = prices[mode][model]
    user = await session.get_user(event_from_user.id)
    free = False
    if model == 'text' and (not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1)):
        free = True
    if model == 'text':
        hint = 'Отправьте текстовое описание картинки, которую вы хотели бы сгенерировать'
    else:
        hint = 'Отправьте фото и к нему текстовое описание изменений, которые вы хотели бы произвести с этим фото'
    return {
        'hint': hint,
        'cost': price if not free else 'Бесплатно'
    }


async def get_image_text(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    model = dialog_manager.dialog_data.get('model')
    mode = dialog_manager.dialog_data.get('mode')
    if model == 'combo':
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста фото и текст изменений к нему')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    result = await generate_wrapper(
        generate_division,
        msg.bot,
        msg.from_user.id,
        text, msg.bot
    )
    if isinstance(result, dict):
        await msg.answer(f'🚨Во время генерации произошла ошибка:\n<code>{result.get("error")}</code>')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    if not result:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    text = f'<b>✅Готово</b>\n<b>Промпт:</b>\n<code>{text}</code>\n\n<a href="https://t.me/Ultragpt_robot">Бот для генерации</a>'
    message = await msg.answer_photo(
        photo=result,
        caption=text
    )
    await msg.bot.copy_message(
        chat_id=config.bot.channel_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    model = dialog_manager.dialog_data.get('model')
    price = prices[mode][model]
    user = await session.get_user(msg.from_user.id)
    if model == 'text' and (not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1)):
        await session.update_last_generate(user.user_id, datetime.datetime.now())
    else:
        await session.update_balance(msg.from_user.id, -price)
    await session.update_gens(msg.from_user.id)
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.start)


async def get_image_prompt(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    model = dialog_manager.dialog_data.get('model')
    mode = dialog_manager.dialog_data.get('mode')
    if model == 'text':
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста только текстовый промпт')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    album: list[Message] = dialog_manager.middleware_data.get('album')
    if len(album) > 1:
        text = album[0].caption
        images = album
    else:
        text = msg.caption
        images = [msg]
    result = await generate_wrapper(
        generate_division,
        msg.bot,
        msg.from_user.id,
        text, msg.bot, images
    )
    if isinstance(result, dict):
        await msg.answer(f'🚨Во время генерации произошла ошибка:\n<code>{result.get("error")}</code>')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    if not result:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    text = f'<b>✅Готово</b>\n<b>Промпт:</b>\n<code>{text}</code>\n\n<a href="https://t.me/Ultragpt_robot">Бот для генерации</a>'
    message = await msg.answer_photo(
        photo=result,
        caption=text
    )
    await msg.bot.copy_message(
        chat_id=config.bot.channel_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    model = dialog_manager.dialog_data.get('model')
    price = prices[mode][model]
    await session.update_balance(msg.from_user.id, -price)
    await session.update_gens(msg.from_user.id)
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.start)


async def get_image_wrong(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    model = dialog_manager.dialog_data.get('model')
    if model == 'text':
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста только текстовый промпт')
    else:
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста фото и текст изменений к нему')


async def video_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    model = clb.data.split('_')[0]
    dialog_manager.dialog_data['model'] = model
    dialog_manager.dialog_data['mode'] = 'video'
    if model in ['seedance']:
        await dialog_manager.switch_to(startSG.video_model_menu)
        return

    await dialog_manager.switch_to(startSG.example_menu)


async def video_model_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    model = dialog_manager.dialog_data.get('model')
    text = ('🤖Seedance\n\n<b>Lite</b> — это как «лайт-версия» приложения: самое простое, чтобы попробовать.\n\n'
            '<b>Pro</b> — это как «премиум»: больше функций, настроек и возможностей для крутого результата.\n\n'
            '☝️Если хочешь быстро и просто - бери Lite. Если любишь «по максимуму» - тогда Pro.')
    buttons = [
        ('Seedance 1 Lite', 'lite'),
        ('Seedance 1 Pro', 'pro')
    ]
    return {
        'text': text,
        'items': buttons
    }


async def sub_model_choose(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['sub_model'] = item_id
    await dialog_manager.switch_to(startSG.example_menu)


async def get_video_prompt_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    model = dialog_manager.dialog_data.get('model')
    sub_model = dialog_manager.dialog_data.get('sub_model')
    if model in ['seedance']:
        model = model + "_" + sub_model
    params = dialog_manager.dialog_data.get('params')
    if not params and model in duration_prices.keys():
        params = {
            'duration': list(duration_prices.get(model).keys())[0],
            'aspect_ratio': '16:9'
        }
        dialog_manager.dialog_data['params'] = params
    params_text = ''
    if params:
        params['price'] = get_video_price(dialog_manager.dialog_data)
        dialog_manager.dialog_data['params'] = params
        params_text = (f' - Соотношение сторон: <b>{params.get("aspect_ratio")}</b>\n - Длительность: '
                       f'<b>{params.get("duration")} сек</b>\n - Стоимость: <b>{params.get("price")} 💎</b>')
    if model == 'seedance':
        hint = 'Отправьте текстовый сценарий видео, которое вы хотели бы сгенерировать'
    else:
        hint = 'Отправьте фото и к нему текстовый сценарий, который вы хотели бы видеть на видео с этим фото'
    return {
        'hint': hint,
        'params': params_text,
        'is_param': bool(params)
    }


async def get_video_text(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    model = dialog_manager.dialog_data.get('model')
    if model == 'kling':
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста фото и текст сценария видео к прикрепленному фото')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    params = dialog_manager.dialog_data.get('params')
    mode = dialog_manager.dialog_data.get('mode')
    sub_model = dialog_manager.dialog_data.get('sub_model')
    user = await session.get_user(msg.from_user.id)
    model_name = model
    if model in ['seedance']:
        model_name = model + "_" + sub_model
    params['model_name'] = model_name
    params['prompt'] = text
    price = get_video_price(dialog_manager.dialog_data)
    if user.balance < price:
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    result = await generate_wrapper(
        generate_on_api,
        msg.bot,
        msg.from_user.id,
        params
    )
    if isinstance(result, dict):
        await msg.answer(f'🚨Во время генерации произошла ошибка:\n<code>{result.get("error")}</code>')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    if not result:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    text = f'<b>✅Готово</b>\n<b>Промпт:</b>\n<code>{text}</code>\n\n<a href="https://t.me/Ultragpt_robot">Бот для генерации</a>'
    message = await msg.answer_video(
        video=result,
        caption=text
    )
    await msg.bot.copy_message(
        chat_id=config.bot.channel_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    await session.update_balance(msg.from_user.id, -price)
    await session.update_gens(msg.from_user.id)
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.start)


async def get_video_prompt(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    model = dialog_manager.dialog_data.get('model')
    if model == 'seedance':
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста только текстовый промпт к сценарию видео')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    params = dialog_manager.dialog_data.get('params')
    mode = dialog_manager.dialog_data.get('mode')
    sub_model = dialog_manager.dialog_data.get('sub_model')
    user = await session.get_user(msg.from_user.id)
    model_name = model
    if model in ['seedance']:
        model_name = model + "_" + sub_model
    params['model_name'] = model_name
    params['prompt'] = msg.caption
    params['image_url'] = await image_to_url(msg.photo[-1], msg.bot)
    price = get_video_price(dialog_manager.dialog_data)
    if user.balance < price:
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    result = await generate_wrapper(
        generate_on_api,
        msg.bot,
        msg.from_user.id,
        params
    )
    if isinstance(result, dict):
        await msg.answer(f'🚨Во время генерации произошла ошибка:\n<code>{result.get("error")}</code>')
        return
    if not result:
        await msg.answer('🚨Во время генерации произошла какая-то ошибка')
        return
    text = f'<b>✅Готово</b>\n<b>Промпт:</b>\n<code>{msg.caption}</code>\n\n<a href="https://t.me/Ultragpt_robot">Бот для генерации</a>'
    message = await msg.answer_video(
        video=result,
        caption=text
    )
    await msg.bot.copy_message(
        chat_id=config.bot.channel_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    await session.update_balance(msg.from_user.id, -price)
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.start)


async def get_video_wrong(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    model = dialog_manager.dialog_data.get('model')
    if model == 'seedance':
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста только текстовый промпт, к сценарию видео')
    else:
        await msg.delete()
        await msg.answer('❗️Отправьте пожалуйста фото и текстовый сценарий к нему')


async def time_choose_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    model = dialog_manager.dialog_data.get('model')
    sub_model = dialog_manager.dialog_data.get('sub_model')
    params = dialog_manager.dialog_data.get('params')
    current_duration = params.get('duration')
    model_name = model
    if model in ['seedance']:
        model_name = model + '_' + sub_model
    buttons = [
        (f'{"✅" if duration == current_duration else ""}{duration} сек', duration)
        for duration in duration_prices.get(model_name).keys()
    ]
    return {
        'items': buttons
    }


async def time_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    params = dialog_manager.dialog_data.get('params')
    duration = int(item_id)
    params['duration'] = duration
    dialog_manager.dialog_data['params'] = params
    await dialog_manager.switch_to(startSG.get_video_prompt)


async def ratio_choose_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    model = dialog_manager.dialog_data.get('model')
    params = dialog_manager.dialog_data.get('params')
    current_ratio = params.get('aspect_ratio')
    buttons = [
        (f'{"✅" if ratio == current_ratio else ""}{ratio} сек', ratio)
        for ratio in model_ratios.get(model)
    ]
    return {
        'items': buttons
    }


async def ratio_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    params = dialog_manager.dialog_data.get('params')
    ratio = item_id
    params['aspect_ratio'] = ratio
    dialog_manager.dialog_data['params'] = params
    await dialog_manager.switch_to(startSG.get_video_prompt)


async def example_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    mode = dialog_manager.dialog_data.get('mode')
    model = dialog_manager.dialog_data.get('model')
    sub_model = dialog_manager.dialog_data.get('sub_model')
    if model in ['seedance']:
        price = prices[mode][model].get(sub_model)
        data = model_examples[mode][model][sub_model]
    else:
        price = prices[mode][model]
        data = model_examples[mode][model]
    media = MediaAttachment(type=data.get('media_type'), path=data.get('media'))
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    free = False
    if model == 'text' and (not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1)):
        free = True
    return {
        'text': data.get('text'),
        'media': media,
        'url': data.get('url'),
        'cost': price if not free else 'Бесплатно'
    }


async def back_choose_model(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    mode = dialog_manager.dialog_data.get('mode')
    if mode == 'image':
        await dialog_manager.switch_to(startSG.image_menu)
    else:
        await dialog_manager.switch_to(startSG.video_menu)


async def balance_check_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(clb.from_user.id)
    switcher = clb.data.split('_')[0]
    print(switcher)
    if switcher == 'task':
        if user.balance < prices['task']:
            dialog_manager.dialog_data['mode'] = switcher
            await dialog_manager.switch_to(startSG.enough_balance)
            return
        await dialog_manager.switch_to(startSG.get_task_photo)
        return
    mode = dialog_manager.dialog_data.get('mode')
    model = dialog_manager.dialog_data.get('model')
    if mode == 'image':
        price = prices[mode][model]
    else:
        sub_model = dialog_manager.dialog_data.get('sub_model')
        if model in ['seedance']:
            price = prices[mode][model].get(sub_model)
        else:
            price = prices[mode][model]
    free = False
    if model == 'text' and (not user.last_generate or user.last_generate < datetime.datetime.now() - datetime.timedelta(days=1)):
        free = True
    if not free and user.balance < price:
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    if mode == 'image':
        await dialog_manager.switch_to(startSG.get_image_prompt)
    else:
        await dialog_manager.switch_to(startSG.get_video_prompt)


async def profile_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    text = (f'<b>👤 Ваш профиль</b>\n<b>💸 Баланс</b>: {user.balance} 💎\n\n<b>🔗 Реферальная программа</b>\n'
            f'<blockquote>Приглашайте друзей и получайте:\n - по 10 💎 за каждого приглашенного\n - 10% от всех '
            f'пополнений💰 вашего реферала в боте — пожизненно!</blockquote>\n\n📎<b>Ваша реф. ссылка:</b> \n'
            f'<code>https://t.me/ultragpt_robot?start={event_from_user.id}</code>\n\n<b>📤 Статистика рефералов</b>'
            f'\n👥 Приглашено: <b>{user.refs}</b>\n💰 Заработано с рефералов: <b>{user.earn} 💎</b>')
    url = f'http://t.me/share/url?url=https://t.me/ultragpt_robot?start={event_from_user.id}'
    media = MediaAttachment(type=ContentType.PHOTO, path='media/profile_img.jpg')
    return {
        'media': media,
        'text': text,
        'url': url
    }


async def enough_balance_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    mode = dialog_manager.dialog_data.get('mode')
    model = dialog_manager.dialog_data.get('model')
    if mode == 'image':
        price = prices[mode][model]
    elif mode == 'task':
        price = prices[mode]
    else:
        sub_model = dialog_manager.dialog_data.get('sub_model')
        price = prices[mode][model].get(sub_model) if sub_model else prices[mode][model]
    url = f'http://t.me/share/url?url=https://t.me/ultragpt_robot?start={event_from_user.id}'
    return {
        'price': price,
        'balance': user.balance,
        'url': url
    }


async def tasks_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    tasks = dialog_manager.dialog_data.get('tasks')
    if not tasks:
        tasks = await get_user_tasks(event_from_user.id, bool(event_from_user.is_premium))
        if not tasks:
            tasks = []
        else:
            dialog_manager.dialog_data['tasks'] = tasks
    page = dialog_manager.dialog_data.get('page')
    if not page:
        page = 0
        dialog_manager.dialog_data['page'] = page
    current_task = tasks[page] if tasks else None

    not_first = False
    not_last = False
    if page != 0:
        not_first = True
    if len(tasks) and page != len(tasks) - 1:
        not_last = True
    amount = 5
    if tasks:
        text = f'<b>Задание № {page + 1}</b>\n'
    else:
        text = '❗️Во время загрузки заданий что-то пошло не так, пожалуйста попробуйте снова'
    return {
        'text': text,
        'url': current_task,
        'amount': amount,
        'page': f'{page + 1}/{len(tasks)}',
        'tasks': bool(tasks),
        'not_first': not_first,
        'not_last': not_last
    }


async def tasks_pager(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    page = dialog_manager.dialog_data.get('page')
    action = clb.data.split('_')[0]
    if action == 'back':
        page -= 1
    else:
        page += 1
    dialog_manager.dialog_data['page'] = page
    await dialog_manager.switch_to(startSG.tasks_menu)


async def check_task(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    tasks: list[str] = dialog_manager.dialog_data.get('tasks')
    page = dialog_manager.dialog_data.get('page')
    current_task = tasks[page]
    status = await check_user_task(clb.from_user.id, current_task)
    if not status:
        await clb.answer('❗️Вы еще не выполнили этого задания')
        return
    amount = 5
    await clb.answer(f'+{amount}💎')
    await session.update_balance(clb.from_user.id, amount)
    tasks.pop(page)
    dialog_manager.dialog_data['tasks'] = tasks
    dialog_manager.dialog_data['page'] = 0
    await dialog_manager.switch_to(startSG.tasks_menu)
