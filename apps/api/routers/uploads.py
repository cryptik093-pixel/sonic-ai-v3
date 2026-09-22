from fastapi import APIRouter, UploadFile, File

from ..services.upload_service import upload_service


router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)


@router.post("/audio")
def upload_audio(
    file: UploadFile = File(...)
):

    return upload_service.save_audio(file)