import os
import zipfile
from io import BytesIO

import pdfkit
from aiogram.types import FSInputFile
from ml.factory import OutputJson, get_ml_response

ALLOWED_LANGUAGES = ("py", "cs", "ts")


def determine_language(path: str):
    splitted = path.rsplit(".", 1)
    if len(splitted) == 2:
        return splitted[1]

    return None


def _unpack_zip_to_tmp(zip_bytes: BytesIO, tmpdirname: str):
    with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
        zip_ref.extractall(tmpdirname)

    languages = {lang: 0 for lang in ALLOWED_LANGUAGES}
    for root, _, files in os.walk(tmpdirname):
        for file in files:
            file_path = os.path.join(root, file)
            lang = determine_language(file_path)
            if lang in ALLOWED_LANGUAGES:
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
