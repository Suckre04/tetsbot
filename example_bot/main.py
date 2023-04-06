import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import psycopg2

# з'єднання з базою даних
conn = psycopg2.connect(
    host="127.0.0.1",
    database="suckre",
    user="suckre",
    password="54642004"
)

load_dotenv()

# ініціалізація бота та диспетчера
bot = Bot(token=os.environ.get('TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# функції для взаємодії з базою даних
async def get_categories():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    cursor.close()
    return categories


async def get_tasks(category_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE category_id = %s", (category_id,))
    tasks = cursor.fetchall()
    cursor.close()
    return tasks


# define a global variable to store the message object
current_message = None


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    categories = await get_categories()

    # створення інлайн-клавіатури для категорій
    keyboard = InlineKeyboardMarkup()
    for category in categories:
        callback_data = f"category_{category[0]}"
        button = InlineKeyboardButton(category[1], callback_data=callback_data)
        keyboard.add(button)

    text = "Оберіть категорію:"
    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)


# обробник вибору категорії
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('category_'))
async def choose_category(callback_query: types.CallbackQuery):
    category_id = int(callback_query.data.split('_')[1])
    tasks = await get_tasks(category_id)

    # створення інлайн-клавіатури для завдань
    keyboard = InlineKeyboardMarkup()
    for task in tasks:
        callback_data = f"task_{task[0]}"
        button = InlineKeyboardButton(task[2], callback_data=callback_data)
        keyboard.add(button)

    text = "Оберіть завдання:"
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=text, reply_markup=keyboard)


# обробник вибору завдання
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('task_'))
async def choose_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split('_')[1])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    cursor.close()

    text = f"Завдання: {task[2]}\n"
    if task[3]:
        text += f"Опис: {task[3]}\n"

    # створення кнопки "Назад" для повернення до списку завдань
    back_button = InlineKeyboardButton("Назад", callback_data="back_to_tasks")
    keyboard = InlineKeyboardMarkup().add(back_button)

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=text, reply_markup=keyboard)


# обробник кнопки "Назад"
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'back_to_tasks')
async def back_to_tasks(callback_query: types.CallbackQuery):
    categories = await get_categories()

    # створення інлайн-клавіатури для категорій
    keyboard = InlineKeyboardMarkup()
    for category in categories:
        callback_data = f"category_{category[0]}"
        button = InlineKeyboardButton(category[1], callback_data=callback_data)
        keyboard.add(button)

    text = "Оберіть категорію:"
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=text, reply_markup=keyboard)


if __name__ == "__main__":
    # запуск
    async def main():
        await dp.start_polling()


    asyncio.run(main())
