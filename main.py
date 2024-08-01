import asyncio
import logging
import sys
import re

from config import tg_bot_token, chat_id

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, KeyboardButton, ReplyKeyboardRemove, FSInputFile


TOKEN = tg_bot_token
form_router = Router()
dp = Dispatcher()
user_dict = {}
user_id: int = 1


class Form(StatesGroup):
    object = State()
    square = State()
    city = State()
    name = State()
    number = State()


# Начинаем наш диалог
@form_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    print(message.from_user.id)
    foto = FSInputFile("Foto.jpg")
    kb = [
        [KeyboardButton(text="Заказать Бесплатную оценку Недвижимости.")]
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)

    await message.answer_photo(photo=foto)
    await message.answer(f"Эксперт по оценки Недвижимости "
                         f"Кузина Ирина тел. +7495000000 ТГ@юзернаме!", reply_markup=keyboard)


@form_router.message(Command(commands='cancel'))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text='Вы вышли из машины состояний\n\n'
             'Чтобы снова перейти к заполнению анкеты - '
             'отправьте команду /start'
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@form_router.message(F.text == 'Заказать Бесплатную оценку Недвижимости.')
@form_router.message(F.text == 'Попробовать еще раз')
async def cmd_keyboard_1(message: Message, state: FSMContext):
    kb = [
        [KeyboardButton(text="Квартира")], [KeyboardButton(text="Загородная недвижимость")],
        [KeyboardButton(text="Коммерческая недвижимость")]
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
    await message.answer("Какую недвижимость Вы хотите оценить?", reply_markup=keyboard)
    await state.set_state(Form.object)


#Проверка ввода площади недвижимости
@form_router.message(StateFilter(Form.object), (F.text != 'Квартира') & (F.text != 'Загородная недвижимость') & (F.text != 'Коммерческая недвижимость'))
async def process_object_invalid(message: Message):
    kb = [
        [KeyboardButton(text="Квартира")], [KeyboardButton(text="Загородная недвижимость")],
        [KeyboardButton(text="Коммерческая недвижимость")]
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
    return await message.reply("Укажите какую недвижимость Вы хотите оценить или напиши /cancel", reply_markup=keyboard)


@form_router.message(Form.object)
@form_router.message(F.text == 'Квартира')
@form_router.message(F.text == 'Загородная недвижимость')
@form_router.message(F.text == 'Коммерческая недвижимость')
async def cmd_keyboard_2(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardRemove(remove_keyboard=True)
    await state.update_data(object=message.text)
    await message.answer("Укажите площадь недвижимости", reply_markup=keyboard)
    await state.set_state(Form.square)


#Проверка ввода площади недвижимости
@form_router.message(StateFilter(Form.square), F.text.isalpha())
async def process_square_invalid(message: Message):
    return await message.reply("Укажите площадь недвижимости или напиши /cancel")


@form_router.message(Form.square)
async def cmd_keyboard_3(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardRemove(remove_keyboard=True)
    await state.update_data(square=message.text)
    await message.answer("Укажите город", reply_markup=keyboard)
    await state.set_state(Form.city)


#Проверка ввода города
@form_router.message(StateFilter(Form.city), F.text.regexp(r'[а-яА-ЯёЁa-zA-Z]*\d+[а-яА-ЯёЁa-zA-Z]*$'))
async def process_city_invalid(message: types.Message):
    return await message.reply("Укажите город или напиши /cancel")


@form_router.message(Form.city)
async def cmd_keyboard_4(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardRemove(remove_keyboard=True)
    await state.update_data(city=message.text)
    await state.set_state(Form.name)
    await message.answer("Укажите ваше имя", reply_markup=keyboard)


#Проверка ввода имени
@form_router.message(StateFilter(Form.name), F.text.regexp(r'[а-яА-ЯёЁa-zA-Z]*\d+[а-яА-ЯёЁa-zA-Z]*$'))
async def process_name_invalid(message: types.Message):
    return await message.reply("Укажите ваше Имя или напиши /cancel")


@form_router.message(Form.name)
async def cmd_keyboard_5(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardRemove(remove_keyboard=True)
    await state.update_data(name=message.text)
    await state.set_state(Form.number)
    await message.answer("Укажите Ваш номер для связи в формате '+7-XXXXXXX'.", reply_markup=keyboard)


#Проверка ввода номера
@form_router.message(StateFilter(Form.number), F.text.isalnum())
async def process_number_invalid(message: types.Message):
    if re.fullmatch(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$', message.text) == False:
        return await message.reply("Укажите Ваш номер для связи или напиши /cancel")
    else:
        return await message.reply("Укажите Ваш номер для связи или напиши /cancel")


@form_router.message(Form.number)
async def show_summary(message: Message, state: FSMContext) -> None:
    await state.update_data(number=message.text)
    global user_id
    user_dict[user_id] = await state.get_data()
    user_dict[user_id]['full_name'] = message.from_user.full_name
    user_dict[user_id]['user_id'] = message.from_user.id
    await state.clear()
    id = user_dict[user_id]['user_id']
    full_name = user_dict[user_id]['full_name']
    object = user_dict[user_id]['object']
    square = user_dict[user_id]['square']
    city = user_dict[user_id]['city']
    name = user_dict[user_id]['name']
    number = user_dict[user_id]['number']
    text_message = (f"Появился новый запрос:\n" 
                    f"Id_заявки: {user_id},\n" 
                    f"id_пользователя: {id},\n" 
                    f"Полное имя: {full_name},\n"
                    f"Объект: {object},\n" 
                    f"Площадь: {square},\n" 
                    f"Город: {city},\n" 
                    f"Имя: {name},\n" 
                    f"Номер: {number}")
    user_id += 1
    kb = [
        [KeyboardButton(text="Попробовать еще раз")]
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
    # Send a message to yourself with the user's username
    await message.bot.send_message(chat_id=chat_id, text=text_message)
    await message.answer("Спасибо. Мы скоро с Вами свяжемся.", reply_markup=keyboard)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())