import os
import shutil
import zipfile
from copy import deepcopy
from io import BytesIO
from uuid import uuid4

import pdfkit
from aiogram.types import FSInputFile
from database import Report
from ml.factory import OutputJson, get_ml_response
from settings.settings import bot_settings


def determine_language(path: str):
    splitted = path.rsplit(".", 1)
    if len(splitted) == 2:
        return splitted[1]

    return None


def _unpack_zip_to_tmp(zip_bytes: BytesIO, tmpdirname: str):
    with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
        zip_ref.extractall(tmpdirname)

    languages = {lang: 0 for lang in bot_settings.ALLOWED_LANGUAGES}
    for root, _, files in os.walk(tmpdirname):
        for file in files:
            file_path = os.path.join(root, file)
            lang = determine_language(file_path)
            if lang in bot_settings.ALLOWED_LANGUAGES:
                languages[lang] += 1

    return max(languages, key=languages.get)


async def _create_pdf_from_template(
    response: OutputJson, pdf_path: str, html_path="/bot/templates/report.html"
):
    pdfkit.from_file(html_path, pdf_path)
    return FSInputFile(pdf_path)


async def handle_file(
    file_bytes: BytesIO, is_file: bool, filename: str, tmpdirname: str
):
    if is_file:
        language = determine_language(filename) or "py"
        with open(f"{tmpdirname}/{filename}", "wb") as f:
            f.write(file_bytes.read())
    else:
        language = _unpack_zip_to_tmp(file_bytes, tmpdirname)

    response = await get_ml_response(tmpdirname, language)

    pdf_path = f"{tmpdirname}/report.pdf"
    pdf = await _create_pdf_from_template(response, pdf_path)

    return pdf, language, response


TOTAL_LINES_UP_DOWN = 3


def create_report(response: OutputJson, tmpdirname: str, pdf: FSInputFile) -> Report:
    ml_response = response.model_dump()
    frontend_response = deepcopy(ml_response)

    for index, code_comment in enumerate(response.code_comments):
        with open(f"{tmpdirname}/example{code_comment.filepath}", "r") as f:
            lines = f.readlines()
            first_number = max(1, code_comment.start_string_number)
            last_number = min(len(lines), code_comment.end_string_number)
            first_index = max(0, first_number - 1 - TOTAL_LINES_UP_DOWN)
            last_index = min(len(lines) - 1, last_number + 2 + TOTAL_LINES_UP_DOWN)
            window_lines = lines[first_index:last_index]

        frontend_response["code_comments"][index]["lines"] = [
            {"order": i + first_index + 1, "text": line}
            for i, line in enumerate(window_lines)
        ]

    random_uuid = uuid4()
    report_file_path = f"/bot/reports/{random_uuid}.pdf"
    shutil.copy(pdf.path, report_file_path)

    return Report(
        id=random_uuid,
        pdf_file_path=report_file_path,
        ml_response=ml_response,
        frontend_response=frontend_response,
    )
