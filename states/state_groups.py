from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class DialogSG(StatesGroup):
    waiting_for_message = State()


class startSG(StatesGroup):
    start = State()

    example_menu = State()

    students_menu = State()
    get_task_photo = State()

    image_menu = State()
    get_image_prompt = State()

    video_menu = State()
    video_model_menu = State()
    get_video_prompt = State()
    time_choose = State()
    ratio_choose = State()

    enough_balance = State()

    gen_prompt_menu = State()

    tasks_menu = State()

    profile = State()

    help = State()


class PaymentSG(StatesGroup):
    choose_rate = State()
    choose_payment = State()
    process_payment = State()


class SubSG(StatesGroup):
    start = State()


class adminSG(StatesGroup):
    start = State()

    get_mail = State()
    get_time = State()
    get_keyboard = State()
    confirm_mail = State()

    rate_menu = State()
    get_rate_amount = State()
    del_rate = State()

    deeplinks_menu = State()
    get_deeplink_name = State()
    deeplink_menu = State()

    admin_menu = State()
    admin_del = State()
    admin_add = State()

    op_menu = State()
    get_op_channel = State()
    get_button_name = State()
    get_button_link = State()
    button_menu = State()
    change_button_text = State()
    change_button_link = State()

    get_user_data = State()
    get_currency_amount = State()
