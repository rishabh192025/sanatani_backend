# app/services/file_service.py
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import filetype

from app.config import settings
from app.models.content import Content # Or a more generic File model if you create one
# from app.models.file_upload import FileUpload # If you have a dedicated FileUpload model from your DBML
# from app.crud.file_upload import file_upload_crud # If using a dedicated CRUD

# For S3 (if you implement it later)
# import boto3
# from botocore.exceptions import NoCredentialsError, ClientError

class FileService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # For S3:
        # self.s3_client = None
        # if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_S3_BUCKET_NAME:
        #     self.s3_client = boto3.client(
        #         "s3",
        #         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        #         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        #         region_name=settings.AWS_REGION,
        #     )

    def _generate_safe_filename(self, filename: str) -> str:
        """Generates a safe filename, appending a UUID to avoid collisions."""
        name, ext = os.path.splitext(filename)
        # Sanitize name part if needed (e.g., remove special chars, limit length)
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)
        return f"{safe_name}_{uuid.uuid4().hex}{ext}"

    async def _save_file_locally(
        self, file: UploadFile, sub_dir: str, safe_filename: str
    ) -> Path:
        """Saves the uploaded file to the local filesystem."""
        destination_dir = self.upload_dir / sub_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        file_path = destination_dir / safe_filename
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close() # Ensure the file stream is closed
        return file_path

    # async def _upload_file_to_s3(
    #     self, file_path: Path, s3_key: str, content_type: Optional[str] = None
    # ) -> str:
    #     """Uploads a file to S3 and returns the S3 URL."""
    #     if not self.s3_client or not settings.AWS_S3_BUCKET_NAME:
    #         raise HTTPException(status_code=500, detail="S3 storage is not configured.")
    #     try:
    #         extra_args = {}
    #         if content_type:
    #             extra_args['ContentType'] = content_type

    #         self.s3_client.upload_file(
    #             str(file_path), settings.AWS_S3_BUCKET_NAME, s3_key, ExtraArgs=extra_args
    #         )
    #         # Construct S3 URL (might vary based on your bucket settings and region)
    #         s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    #         return s3_url
    #     except FileNotFoundError:
    #         raise HTTPException(status_code=500, detail="Source file not found for S3 upload.")
    #     except NoCredentialsError:
    #         raise HTTPException(status_code=500, detail="S3 credentials not available.")
    #     except ClientError as e:
    #         # Log e
    #         raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")


    async def upload_content_file(
        self, db: AsyncSession, content_obj: Content, file: UploadFile, upload_dir_prefix: str = "content_main"
    ) -> Tuple[str, int]:
        """
        Handles uploading a main file for a content object.
        Returns (file_url, file_size_bytes).
        Updates the content_obj with file_url and file_size.
        """
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds limit of {settings.MAX_FILE_SIZE // (1024*1024)}MB."
            )

        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_extension}' not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # Optional MIME detection with filetype
        # file_header = await file.read(2048)
        # await file.seek(0)
        # kind = filetype.guess(file_header)
        # if kind is None:
        #     raise HTTPException(status_code=400, detail="Could not detect file type")


        safe_filename = self._generate_safe_filename(file.filename)
        
        # For now, always save locally. S3 logic can be added.
        # if self.s3_client and settings.AWS_S3_BUCKET_NAME:
        #     # Save locally temporarily, then upload to S3, then remove local temp
        #     temp_local_path = await self._save_file_locally(file, "temp_uploads", safe_filename)
        #     s3_object_key = f"{upload_dir_prefix}/{content_obj.id}/{safe_filename}"
        #     final_file_url = await self._upload_file_to_s3(temp_local_path, s3_object_key, file.content_type)
        #     temp_local_path.unlink() # Remove temp local file
        # else:
            # Save locally permanently
        local_file_path = await self._save_file_locally(file, f"{upload_dir_prefix}/{content_obj.id}", safe_filename)
        # For local serving, the URL would be relative to a static files mount point
        # or served via a dedicated endpoint. For simplicity, storing path.
        # In a real app, this would be a URL accessible by the client.
        final_file_url = f"/static/{upload_dir_prefix}/{content_obj.id}/{safe_filename}" # Placeholder URL

        file_size_bytes = file.size

        # Update the content object
        content_obj.file_url = str(final_file_url) # Store the relative URL or S3 URL
        content_obj.file_size = file_size_bytes
        
        db.add(content_obj)
        await db.commit()
        await db.refresh(content_obj)
        
        return str(final_file_url), file_size_bytes

    async def upload_generic_file(
        self,
        file: UploadFile,
        sub_folder: str, # e.g., "avatars", "cover_images"
        # related_entity_id: Optional[uuid.UUID] = None # If tracking via FileUpload model
    ) -> Tuple[str, str, int]: # (final_url, mime_type, file_size)
        """Generic file uploader, returns URL, MIME type, and size."""
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")

        # Determine MIME type
        # Read a small chunk to determine MIME type without loading the whole file in memory
        # Be careful with file.file.read() as it consumes the stream
        # For a more robust solution, consider passing the file path after saving it once
        file_content_for_mime = await file.read(2048) # Read first 2KB
        await file.seek(0) # Reset file pointer
        kind = filetype.guess(file_header)
        if kind is None:
            raise HTTPException(status_code=400, detail="Could not detect MIME type")
        mime_type = kind.mime

        safe_filename = self._generate_safe_filename(file.filename)

        # Simplified local storage path:
        storage_path = self.upload_dir / sub_folder
        storage_path.mkdir(parents=True, exist_ok=True)
        full_path = storage_path / safe_filename

        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # This URL would typically be served by your app or a CDN
        # e.g., /static/avatars/some_file_uuid.jpg
        relative_url = f"/static/{sub_folder}/{safe_filename}" # Placeholder

        # If using S3:
        # s3_key = f"{sub_folder}/{safe_filename}"
        # s3_url = await self._upload_file_to_s3(full_path, s3_key, mime_type)
        # full_path.unlink() # Remove local copy after S3 upload if desired
        # return s3_url, mime_type, file.size

        return relative_url, mime_type, file.size


# Create an instance of the service
file_service = FileService()