from copy import deepcopy
import shutil
import tempfile
from io import BytesIO
from uuid import UUID, uuid4

from ml.factory import list_files_in_directory
from database import Report, Session
from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from schemas.review import ReviewSchema, UploadFileReponseSchema
from services.review import ALLOWED_LANGUAGES, determine_language, handle_file
from sqlalchemy import select

router = APIRouter()


@router.post("/upload/")
async def upload_file(
    file: UploadFile,
    session: Session,
) -> UploadFileReponseSchema:
    is_file = determine_language(file.filename) in ALLOWED_LANGUAGES
    if not file.filename.endswith("zip") and not is_file:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    with tempfile.TemporaryDirectory() as tmpdirname:
        pdf, language, response = await handle_file(
            BytesIO(await file.read()), is_file, file.filename, tmpdirname
        )
        ml_response = response.model_dump()
        frontend_response = deepcopy(ml_response)

        for index, code_comment in enumerate(response.code_comments):
            with open(f"{tmpdirname}/example{code_comment.filepath}", "r") as f:
                lines = f.readlines()
                first_number = max(1, code_comment.start_string_number)
                last_number = min(len(lines), code_comment.end_string_number)
                first_index = max(0, first_number - 4)
                last_index = min(len(lines) - 1, last_number + 4)
                window_lines = lines[first_index: last_index]

            del frontend_response["code_comments"][index]["start_string_number"]
            del frontend_response["code_comments"][index]["end_string_number"]
            frontend_response["code_comments"][index]["lines"] = [
                {"order": i + first_index + 1, "text": line} for i, line in enumerate(window_lines)
            ]

        print(frontend_response)

        random_uuid = uuid4()
        report_file_path = f"/bot/reports/{random_uuid}.pdf"
        shutil.copy(pdf.path, report_file_path)

        report = Report(
            id=random_uuid,
            pdf_file_path=report_file_path,
            ml_response=ml_response,
            frontend_response=frontend_response,
        )

    session.add(report)
    await session.commit()

    return UploadFileReponseSchema(report_id=report.id)


@router.get("/report/{report_id}")
async def get_report(session: Session, report_id: UUID) -> FileResponse:
    get_report_query = select(Report).filter(Report.id == report_id)
    report = (await session.execute(get_report_query)).scalars().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    return FileResponse(report.pdf_file_path, media_type="application/pdf")


@router.get("/review/{report_id}")
async def get_review(session: Session, report_id: UUID) -> ReviewSchema:
    get_report_query = select(Report).filter(Report.id == report_id)
    report = (await session.execute(get_report_query)).scalars().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    return ReviewSchema(
        id=report.id,
        titles=report.frontend_response.get("titles") or [],
        code_comments=report.frontend_response.get("code_comments") or [],
        project_comments=report.frontend_response.get("project_comments") or [],
    )
