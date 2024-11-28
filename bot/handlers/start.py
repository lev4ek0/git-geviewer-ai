from aiogram import F, Bot, Router, types
from aiogram.filters import Command
from aiogram.types import ContentType, FSInputFile


import pdfkit

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = "Добро пожаловать, меня зовут Норберт! Загрузите, пожалуйста zip архив с кодом, я подскажу как написать лучше"
    await message.answer(text=text)


@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    document = message.document

    if document.file_name.endswith("zip"):
        try:
            pdf_path = "/bot/templates/report.pdf"
            pdfkit.from_file("/bot/templates/report.html", pdf_path)
            pdf = FSInputFile(pdf_path)

            await message.answer_document(pdf)

        except Exception as e:
            await message.reply(f"Ошибка при конвертации: {e}")
    else:
        await message.reply("Пожалуйста, отправьте файл с расширением .zip")

