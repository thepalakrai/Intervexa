import os
import uuid
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from pypdf import PdfReader

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
RESUME_CONTAINER = os.getenv("BLOB_CONTAINER_RESUMES", "resumes")
JD_CONTAINER = os.getenv("BLOB_CONTAINER_JDS", "job-descriptions")

_blob_service_client = None


def get_blob_service_client() -> BlobServiceClient:
    global _blob_service_client
    if _blob_service_client is None:
        if not CONNECTION_STRING:
            raise RuntimeError(
                "AZURE_STORAGE_CONNECTION_STRING is not set. Check your .env file."
            )
        _blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    return _blob_service_client


def upload_file(container_name: str, file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    """
    Uploads a file to the given container.
    Returns (blob_name, blob_url).
    """
    client = get_blob_service_client()
    container_client = client.get_container_client(container_name)

    extension = original_filename.split(".")[-1] if "." in original_filename else "bin"
    blob_name = f"{uuid.uuid4()}.{extension}"

    container_client.upload_blob(name=blob_name, data=file_bytes, overwrite=True)

    blob_url = f"{client.primary_endpoint}{container_name}/{blob_name}"
    return blob_name, blob_url


def upload_resume(file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    return upload_file(RESUME_CONTAINER, file_bytes, original_filename)


def upload_job_description(file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    return upload_file(JD_CONTAINER, file_bytes, original_filename)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Basic text extraction for straightforward text PDFs.
    Scanned/image PDFs will need OCR later - not handled here yet.
    """
    reader = PdfReader(BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text_parts.append(extracted)
    return "\n".join(text_parts)
