from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


dialog_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='На главное меню', callback_data='back_main')]]
)
