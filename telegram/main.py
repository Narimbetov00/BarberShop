import aiohttp
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import os

load_dotenv()
BASE_URL = "http://localhost:8000/api/v1"
Queue_Url = "/clients"


bot = Bot(token=os.getenv("BOT_TOKEN"),default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

class ClientForm(StatesGroup):
    waiting_for_phone = State()

async def start_menu():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="📥 Oshiret Aliw")
    keyboard.button(text="📥 Oshiretdi biliw")
    return keyboard.as_markup(resize_keyboard=True)


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Assalawma aleykum Botga qosh kelipsiz!Tomendegilerden birin saylan:", 
                         reply_markup=await start_menu())

@dp.message(lambda message: message.text == "📥 Oshiret Aliw")
async def get_queue(message: Message, state: FSMContext):
    await message.answer("Telefon raqamingizni yuboring:")
    await state.set_state(ClientForm.waiting_for_phone)

@dp.message(lambda message: message.text == "📥 Oshiretdi biliw")
async def get_queue(message: Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        chat_id = message.from_user.id
        async with session.get(f"{BASE_URL+Queue_Url}/{chat_id}") as response:
            data = await response.json()
        if response.status == 200:
            await message.answer(f"sizdin oshiretiniz: <b>{data['data']['queue']}</b>",parse_mode="HTML")
        else:
            await message.answer(f"⚠️{data['message']}")

@dp.message(ClientForm.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text
    chat_id = message.from_user.id
    username_tg = message.from_user.username or f"+{phone}"

    async with aiohttp.ClientSession() as session:
        async with session.post(BASE_URL+Queue_Url, json={"chat_id": chat_id, "phone": phone, "username_tg": username_tg}) as response:
            data = await response.json()
    
    if response.status == 201:
        queue_number = data["data"]["queue"]
        await message.answer(f"✅ Siz oshiretge alindiniz!\nOshiretiniz: {queue_number}")
    else:
        await message.answer(f"⚠️ {data['message']}")

    await state.clear()



async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
