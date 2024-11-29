import os
import tempfile
import zipfile
from io import BytesIO

import pdfkit
from aiogram import Bot, F, Router, types
from aiogram.types import ContentType, FSInputFile
from handlers.ml_response_factory import OutputJson, get_ml_response

router = Router()


ALLOWED_LANGUAGES = ("py", "cs", "ts")


def determine_language(path: str):
    splitted = path.rsplit(".", 1)
    if len(splitted) == 2:
        return splitted[1]
    return None

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
    
    languages = {
        lang: 0 for lang in ALLOWED_LANGUAGES
    }
    for root, _, files in os.walk(tmpdirname):
        for file in files:
            file_path = os.path.join(root, file)
            lang = determine_language(file_path)
            if lang in ALLOWED_LANGUAGES:
                languages[lang] += 1

    return max(languages, key=languages.get)


async def create_pdf_from_template(response: OutputJson, pdf_path: str):
    pdfkit.from_file("/bot/templates/report.html", pdf_path)
    return FSInputFile(pdf_path)


async def handle_file(message: types.Message, file_bytes: BytesIO, is_file: bool, filename: str):
    with tempfile.TemporaryDirectory() as tmpdirname:
        if is_file:
            language = determine_language(filename) or "py"
            with open(f"{tmpdirname}/{filename}", "wb") as f:
                f.write(file_bytes.read())
        else:
            language = unpack_zip_to_tmp(file_bytes, tmpdirname)

        response = await get_ml_response(tmpdirname, language)

        pdf_path = f"{tmpdirname}/report.pdf"
        pdf = await create_pdf_from_template(response, pdf_path)

        await message.answer_document(pdf)
        # await message.answer(str(response.model_dump()))
        await message.answer(language)


@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: types.Message, bot: Bot):
    document = message.document

    is_file = determine_language(document.file_name) in ALLOWED_LANGUAGES
    if document.file_name.endswith("zip") or is_file:
        try:
            file_bytes = await download_document(bot, document.file_id)
            await handle_file(message, file_bytes, is_file, document.file_name)
        except Exception as e:
            await message.reply(f"Ошибка при конвертации: {e}")
    else:
        await message.reply("Пожалуйста, отправьте файл с расширением .zip")
