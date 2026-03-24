import aiofiles
import uuid
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import os
import mimetypes

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from src.api.auth import get_current_active_user, User
from src.api.middleware import limiter
from src.services.s3_service import S3Service
from src.config import settings


# In-memory storage for uploaded files (in production, use database)
uploaded_files_storage = {}


router = APIRouter(tags=["upload"])


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_path: str
    file_size: int
    upload_timestamp: datetime
    content_type: str


class FileListResponse(BaseModel):
    files: List[UploadResponse]
    total_count: int


@router.get("/")
async def upload_info():
    """Upload service information."""
    return {
        "service": "File Upload Service",
        "endpoints": {
            "upload_resume": "POST /resume",
            "demo_upload": "POST /demo (no auth required)",
            "list_files": "GET /resume/list", 
            "preview_text": "GET /resume/{file_id}/preview",
            "delete_file": "DELETE /resume/{file_id}",
            "download_file": "GET /resume/{file_id}/download"
        },
        "supported_formats": [".pdf", ".doc", ".docx", ".txt"],
        "max_file_size": "10MB",
        "note": "Most endpoints require authentication. Use /demo for testing."
    }


# Allowed file types for resume uploads
ALLOWED_RESUME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def extract_text_from_file(content: bytes, content_type: str) -> str:
    """Extract text content from uploaded file."""
    try:
        if content_type == "text/plain":
            return content.decode('utf-8', errors='ignore')
        elif content_type == "application/pdf" and PDF_AVAILABLE:
            pdf_stream = io.BytesIO(content)
            pdf_reader = PdfReader(pdf_stream)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        else:
            # For unsupported file types, return metadata
            return f"[File type {content_type} - Content extraction not fully supported. File size: {len(content)} bytes]"
    except Exception as e:
        return f"[Error extracting text from {content_type}: {str(e)}]"


def validate_resume_file(file: UploadFile) -> None:
    """Validate uploaded resume file."""
    if file.content_type not in ALLOWED_RESUME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. "
                   f"Allowed types: {', '.join(ALLOWED_RESUME_TYPES)}"
        )
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )


@router.post("/resume", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a resume file."""
    
    # Validate file
    validate_resume_file(file)
    
    # Generate unique file ID and path
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1].lower()
    file_path = f"resumes/{current_user.id}/{file_id}{file_extension}"
    
    try:
        # Read file content
        content = await file.read()
        
        # TODO: In production, upload to S3 here
        # For development, we'll just simulate the upload
        
        # Extract text content from the file
        extracted_text = extract_text_from_file(content, file.content_type)
        
        # Store file metadata in memory (in production, use database)
        upload_data = {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "upload_timestamp": datetime.utcnow(),
            "content_type": file.content_type,
            "user_id": current_user.id,
            "file_content": extracted_text
        }
        
        # Store by user
        if current_user.id not in uploaded_files_storage:
            uploaded_files_storage[current_user.id] = []
        uploaded_files_storage[current_user.id].append(upload_data)
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            upload_timestamp=datetime.utcnow(),
            content_type=file.content_type
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )
    finally:
        await file.close()


@router.post("/demo")
async def demo_upload(
    file: UploadFile = File(...)
):
    """Demo file upload endpoint (no authentication required for testing)."""
    
    try:
        # Basic file validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
            
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        # Generate a demo response
        file_id = str(uuid.uuid4())
        
        return {
            "message": "Demo upload successful",
            "file_id": file_id,
            "filename": file.filename,
            "file_size": len(content),
            "content_type": file.content_type,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "note": "This is a demo endpoint. File was not actually stored."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )
    finally:
        await file.close()


@router.get("/resume/list", response_model=FileListResponse)
async def list_user_resumes(
    current_user: User = Depends(get_current_active_user),
    limit: int = 10,
    offset: int = 0
):
    """List user's uploaded resumes."""
    
    # Get user's uploaded files from storage
    user_files = uploaded_files_storage.get(current_user.id, [])
    
    # Convert to UploadResponse objects
    file_responses = []
    for file_data in user_files:
        file_responses.append(UploadResponse(
            file_id=file_data["file_id"],
            filename=file_data["filename"],
            file_path=file_data["file_path"],
            file_size=file_data["file_size"],
            upload_timestamp=file_data["upload_timestamp"],
            content_type=file_data["content_type"]
        ))
    
    # Sort by upload timestamp (newest first)
    file_responses.sort(key=lambda x: x.upload_timestamp, reverse=True)
    
    # Apply pagination
    paginated_files = file_responses[offset:offset + limit]
    
    return FileListResponse(
        files=paginated_files,
        total_count=len(file_responses)
    )


@router.get("/resume/{file_id}/preview")
async def preview_resume_text(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Preview extracted text content from an uploaded resume."""
    
    # Get user's files
    user_files = uploaded_files_storage.get(current_user.id, [])
    
    # Find the requested file
    file_data = None
    for uploaded_file in user_files:
        if uploaded_file["file_id"] == file_id:
            file_data = uploaded_file
            break
    
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "content_type": file_data["content_type"],
        "extracted_text": file_data.get("file_content", "[No text content available]"),
        "text_length": len(file_data.get("file_content", "")),
        "note": "This is the text that will be used for analysis"
    }


@router.delete("/resume/{file_id}")
async def delete_resume(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a user's resume file."""
    
    # Get user's files
    user_files = uploaded_files_storage.get(current_user.id, [])
    
    # Find the file to delete
    file_to_delete = None
    file_index = None
    for i, file_data in enumerate(user_files):
        if file_data["file_id"] == file_id:
            file_to_delete = file_data
            file_index = i
            break
    
    if not file_to_delete:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # TODO: In production, delete from S3 here
        # await s3_service.delete_file(file_to_delete["file_path"])
        
        # Remove from in-memory storage
        uploaded_files_storage[current_user.id].pop(file_index)
        
        # Delete metadata from database
        # await delete_file_metadata(file_id)
        
        return {"message": "File deleted successfully", "file_id": file_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/resume/{file_id}/download")
async def download_resume(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    s3_service: S3Service = Depends()
):
    """Generate a presigned URL for downloading a resume."""
    
    # In real implementation, verify file ownership
    # file_metadata = await get_file_metadata(file_id)
    # if file_metadata.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    try:
        s3_key = f"resumes/{current_user.id}/{file_id}.pdf"  # Would get from database
        download_url = await s3_service.generate_presigned_url(
            key=s3_key,
            expiration=3600  # 1 hour
        )
        
        return {"download_url": download_url, "expires_in": 3600}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(e)}"
        )