#
import boto3
from uuid import uuid4
from urllib.parse import quote_plus
from app.config import settings


s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

def upload_file_to_s3(file_obj, filename: str, content_type: str = "application/octet-stream") -> str:
    unique_filename = f"{uuid4()}_{filename}"
    s3_client.upload_fileobj(
        file_obj,
        settings.AWS_S3_BUCKET_NAME,
        unique_filename,
        ExtraArgs={"ContentType": content_type},
    )
    encoded_filename = quote_plus(unique_filename)
    s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{encoded_filename}"
    return s3_url


def generate_presigned_url(filename: str, content_type: str = "application/octet-stream", expires_in: int = 600) -> str:
    """
    Generate a presigned S3 URL that allows file upload directly to S3.
    :param filename: The desired file name to store in S3
    :param content_type: MIME type of the file
    :param expires_in: How long (in seconds) the URL is valid. Default is 10 minutes.
    :return: Presigned URL (string)
    """
    unique_filename = f"{uuid4()}_{filename}"
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET_NAME,
                'Key': unique_filename,
                'ContentType': content_type,
            },
            ExpiresIn=expires_in,
        )
        return url
    except Exception as e:
        raise RuntimeError(f"Failed to generate presigned URL: {e}")
