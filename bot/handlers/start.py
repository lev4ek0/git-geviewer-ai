from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = "Добро пожаловать, меня зовут Норберт! Загрузите, пожалуйста, архив с кодом или файл, я подскажу, как написать лучше"
    await message.answer(text=text)
