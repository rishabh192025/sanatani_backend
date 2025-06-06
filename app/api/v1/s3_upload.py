from fastapi import APIRouter, File, UploadFile, HTTPException

from app.utils.s3_utils import upload_file_to_s3


router = APIRouter()

@router.post("")
async def upload_to_s3(file: UploadFile = File(...)):
    try:
        s3_url = upload_file_to_s3(file.file, file.filename, file.content_type)
        return {"url": s3_url, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
