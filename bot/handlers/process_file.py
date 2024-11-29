import tempfile
from io import BytesIO

from aiogram import Bot, F, Router, types
from aiogram.types import ContentType
from services.review import (
    ALLOWED_LANGUAGES,
    _create_pdf_from_template,
    determine_language,
    handle_file,
)

router = Router()


async def download_document(bot: Bot, file_id: str) -> BytesIO:
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    zip_file_bytes = BytesIO()

    await bot.download_file(file_path, zip_file_bytes)
    zip_file_bytes.seek(0)

    return zip_file_bytes


@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: types.Message, bot: Bot):
    document = message.document

    is_file = determine_language(document.file_name) in ALLOWED_LANGUAGES
    if document.file_name.endswith("zip") or is_file:
        try:
            file_bytes = await download_document(bot, document.file_id)
            with tempfile.TemporaryDirectory() as tmpdirname:
                pdf, language, response = await handle_file(
                    file_bytes, is_file, document.file_name, tmpdirname
                )

                await message.answer_document(pdf)
                # await message.answer(str(response.model_dump()))
                await message.answer(language)

        except Exception as e:
            await message.reply(f"Ошибка при конвертации")
    elif document.file_name.endswith("html"):
        file_bytes = await download_document(bot, document.file_id)
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(f"{tmpdirname}/1.html", "wb") as f:
                f.write(file_bytes.read())

            pdf_path = f"{tmpdirname}/report.pdf"
            pdf = await _create_pdf_from_template(1, pdf_path, f"{tmpdirname}/1.html")

            await message.answer_document(pdf)
    else:
        await message.reply("Пожалуйста, отправьте файл с расширением .zip")
