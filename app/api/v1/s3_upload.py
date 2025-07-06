# File: app/api/v1/s3_upload.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends

from app.schemas import PresignRequest
from app.utils.s3_utils import generate_presigned_url
from app.utils.s3_utils import upload_file_to_s3
from app.dependencies import get_current_active_admin  # Ensure this is defined in your dependencies
from app.models.user import User  # For type hinting

router = APIRouter()

@router.post("")
async def upload_to_s3(
    current_user: User = Depends(get_current_active_admin),  # Use specific dependency
    file: UploadFile = File(...)
):
    try:
        s3_url = upload_file_to_s3(file.file, file.filename, file.content_type)
        return {"url": s3_url, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/generate-presigned-url")
async def get_presigned_upload_url(
    payload: PresignRequest,
    current_user: User = Depends(get_current_active_admin)  # Use specific dependency
):
    try:
        url = generate_presigned_url(payload.filename, payload.content_type)
        return {"upload_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate presigned URL: {str(e)}")

