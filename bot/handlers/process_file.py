import tempfile
from io import BytesIO

import pdfkit
from aiogram import Bot, F, Router, types
from aiogram.types import ContentType, FSInputFile
from database.connection import PostgresConnection
from services.review import determine_language, handle_file
from settings.settings import bot_settings
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


async def download_document(bot: Bot, file_id: str) -> BytesIO:
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    zip_file_bytes = BytesIO()

    await bot.download_file(file_path, zip_file_bytes)
    zip_file_bytes.seek(0)

    return zip_file_bytes


@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(
    message: types.Message, bot: Bot, session: PostgresConnection
):
    document = message.document

    is_file = determine_language(document.file_name) in bot_settings.ALLOWED_LANGUAGES
    if document.file_name.endswith("zip") or is_file:
        # try:
        file_bytes = await download_document(bot, document.file_id)
        with tempfile.TemporaryDirectory() as tmpdirname:
            await message.answer(
                "Вы успешно загрузили файл! Пожалуйста, подождите несколько минут, пока я его не обработаю"
            )
            pdf, language, response, report = await handle_file(
                file_bytes, is_file, document.file_name, tmpdirname
            )

            repord_link = f"{bot_settings.BASE_API_URL}/api/review/{report.id}"

            async with AsyncSession(session.engine) as async_session:
                async_session.add(report)
                await async_session.commit()

            await message.answer_document(pdf)
            # await message.answer(str(response.model_dump()))
            await message.answer(repord_link)

        # except Exception as e:
        #     await message.reply(f"Ошибка при конвертации")
    elif document.file_name.endswith("html"):
        file_bytes = await download_document(bot, document.file_id)
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(f"{tmpdirname}/1.html", "wb") as f:
                f.write(file_bytes.read())

            pdf_path = f"{tmpdirname}/report.pdf"
            pdfkit.from_file(f"{tmpdirname}/1.html", pdf_path)
            pdf = FSInputFile(pdf_path)

            await message.answer_document(pdf)
    else:
        await message.reply("Пожалуйста, отправьте файл с расширением .zip")
