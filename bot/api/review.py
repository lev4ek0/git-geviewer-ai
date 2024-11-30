import tempfile
from io import BytesIO
from uuid import UUID

from database import Report, Session
from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from schemas.review import ReviewSchema, UploadFileReponseSchema
from services.review import determine_language, handle_file
from settings.settings import bot_settings
from sqlalchemy import select

router = APIRouter()


@router.post("/upload/")
async def upload_file(
    file: UploadFile,
    session: Session,
) -> UploadFileReponseSchema:
    is_file = determine_language(file.filename) in bot_settings.ALLOWED_LANGUAGES
    if not file.filename.endswith("zip") and not is_file:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    with tempfile.TemporaryDirectory() as tmpdirname:
        pdf, language, response, report = await handle_file(
            BytesIO(await file.read()), is_file, file.filename, tmpdirname
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
