# File: app/api/v1/s3_upload.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi import Query

from app.schemas import PresignRequest
from app.utils.s3_utils import generate_presigned_url
from app.utils.s3_utils import upload_file_to_s3


router = APIRouter()

@router.post("")
async def upload_to_s3(file: UploadFile = File(...)):
    try:
        s3_url = upload_file_to_s3(file.file, file.filename, file.content_type)
        return {"url": s3_url, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/generate-presigned-url")
async def get_presigned_upload_url(payload: PresignRequest):
    try:
        url = generate_presigned_url(payload.filename, payload.content_type)
        return {"upload_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate presigned URL: {str(e)}")

