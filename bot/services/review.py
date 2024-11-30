import itertools
import os
import shutil
import zipfile
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pdfkit
import pytz
from aiogram.types import FSInputFile
from database import Report
from jinja2 import Environment, FileSystemLoader
from ml.factory import OutputJson, get_ml_response
from schemas.review import ReviewSchema
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
    filename: str,
    tmpdirname: str,
    response: ReviewSchema,
    pdf_path: str,
    html_path="/bot/templates/report.html",
):
    template_dir = os.path.dirname(html_path)
    template_name = os.path.basename(html_path)

    env = Environment(loader=FileSystemLoader(template_dir))

    template = env.get_template(template_name)

    moscow_tz = pytz.timezone("Europe/Moscow")
    now = datetime.now(moscow_tz)

    # Форматируем дату и время
    formatted_date = now.strftime("%d.%m.%Y, %H:%M:%S")
    title_remarks = defaultdict(list)
    for comment in itertools.chain(response.code_comments, response.project_comments):
        title_remarks[comment.title].append(comment)

    render_context = {
        "name": filename,
        "date": formatted_date,
        "total_remarks": len(response.code_comments) + len(response.project_comments),
        "title_remarks": [
            [title, len(remarks)] for title, remarks in title_remarks.items()
        ],
        "title_infos": [
            [
                title,
                [
                    remark.comment
                    for remark in remarks
                    if not hasattr(remark, "suggestion")
                ],
                [
                    [
                        remark.filepath,
                        remark.comment,
                        "".join(
                            [
                                line.text.replace("<", "&lt;").replace(" ", "&nbsp;")
                                for line in remark.lines
                            ]
                        ),
                        (remark.suggestion or "")
                        .replace("<", "&lt;")
                        .replace(" ", "&nbsp;")
                        .replace("```python", "")
                        .replace("```", ""),
                        remark.start_string_number - bot_settings.TOTAL_LINES_UP_DOWN,
                    ]
                    for remark in remarks
                    if hasattr(remark, "suggestion")
                ],
            ]
            for title, remarks in title_remarks.items()
        ],
    }
    print(render_context)
    rendered_html = template.render(render_context)

    html_output_path = os.path.join(tmpdirname, "output.html")
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    pdfkit.from_file(html_output_path, pdf_path)
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
    frontend_response, ml_response = create_report(filename, response, tmpdirname)

    random_uuid = uuid4()
    report_file_path = f"/bot/reports/{random_uuid}.pdf"

    report = Report(
        id=random_uuid,
        pdf_file_path=report_file_path,
        ml_response=ml_response,
        frontend_response=frontend_response,
    )
    pdf_path = f"{tmpdirname}/report.pdf"
    frontend = ReviewSchema(**{**report.frontend_response, "id": str(random_uuid)})
    pdf = await _create_pdf_from_template(filename, tmpdirname, frontend, pdf_path)
    shutil.copy(pdf.path, report_file_path)

    return pdf, language, response, report


def create_report(filename: str, response: OutputJson, tmpdirname: str) -> Report:
    ml_response = response.model_dump()
    frontend_response = deepcopy(ml_response)

    for index, code_comment in enumerate(response.code_comments):
        try:
            with open(
                f"{tmpdirname}/{filename.replace('.zip', '')}/{code_comment.filepath}",
                "r",
            ) as f:
                lines = f.readlines()
                first_number = max(1, code_comment.start_string_number)
                last_number = min(len(lines), code_comment.end_string_number)
                first_index = max(
                    0, first_number - 1 - bot_settings.TOTAL_LINES_UP_DOWN
                )
                last_index = min(
                    len(lines) - 1, last_number + 2 + bot_settings.TOTAL_LINES_UP_DOWN
                )
                window_lines = lines[first_index:last_index]

            frontend_response["code_comments"][index]["lines"] = [
                {"order": i + first_index + 1, "text": line}
                for i, line in enumerate(window_lines)
            ]
        except Exception:
            frontend_response["code_comments"][index]["lines"] = [
                {
                    "order": 1,
                    "text": "",
                }
            ]
    return frontend_response, ml_response
