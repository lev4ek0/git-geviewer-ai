import tempfile
import zipfile
from io import BytesIO

import pdfkit
from aiogram import Bot, F, Router, types
from aiogram.types import ContentType, FSInputFile
from handlers.ml_response_factory import OutputJson, get_ml_response

router = Router()


async def download_document(bot: Bot, file_id: str) -> BytesIO:
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    zip_file_bytes = BytesIO()

    await bot.download_file(file_path, zip_file_bytes)
    zip_file_bytes.seek(0)

    return zip_file_bytes


def unpack_zip_to_tmp(zip_bytes: BytesIO, tmpdirname: str):
    with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
        zip_ref.extractall(tmpdirname)


async def create_pdf_from_template(pdf_path: str, response: OutputJson):
    pdfkit.from_file("bot/templates/report.html", pdf_path)
    return FSInputFile(pdf_path)


async def handle_zip_file(message: types.Message, zip_bytes: BytesIO):
    with tempfile.TemporaryDirectory() as tmpdirname:
        unpack_zip_to_tmp(zip_bytes, tmpdirname)

        response = await get_ml_response(tmpdirname)

        pdf_path = f"{tmpdirname}/report.pdf"
        pdf = await create_pdf_from_template(response, pdf_path)

        await message.answer_document(pdf)
        await message.answer(str(response.model_dump()))


@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: types.Message, bot: Bot):
    document = message.document

    if document.file_name.endswith("zip"):
        try:
            zip_file_bytes = await download_document(bot, document.file_id)
            await handle_zip_file(message, zip_file_bytes)
        except Exception as e:
            await message.reply(f"Ошибка при конвертации: {e}")
    else:
        await message.reply("Пожалуйста, отправьте файл с расширением .zip")
