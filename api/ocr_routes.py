# api/ocr_routes.py
"""
OCR API routes for ImageAI.
Handles image, PDF, document, and video OCR endpoints.

This module refactors upload.py into clean API routes.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from api.schemas import OCRResponse, FieldExtractionResponse
from utils.file_handler import extract_text, extract_keywords
from core.field_extractor import extract_structured_fields, extract_invoice_fields, extract_form_fields
from utils.logger import log

router = APIRouter()


@router.post("/upload", response_class=JSONResponse)
async def upload_and_ask(files: List[UploadFile] = File(...), question: str = Form(...)):
    """
    Legacy endpoint for backward compatibility.
    Upload files and ask a question about the content.
    """
    log.info("Upload endpoint hit")
    all_text_str = ""
    all_text_list = []

    readable_files = []
    failed_files = []

    for file in files:
        try:
            result = await extract_text(file)  # returns dict: success, message, text
        except Exception as e:
            log.error(f"Failed to extract text from {file.filename}: {e}")
            failed_files.append({"filename": file.filename, "reason": str(e)})
            continue

        if not result["success"]:
            failed_files.append({"filename": file.filename, "reason": result["message"]})
            all_text_list.append({"filename": file.filename, "text": result["message"], "valid": False})
            continue

        # OCR succeeded
        readable_files.append(result["text"])
        all_text_list.append({"filename": file.filename, "text": result["text"], "valid": True})

    # If all files failed, return JSON immediately
    if not readable_files:
        message = "Details: " + ", ".join([f"{f['filename']} ({f['reason']})" for f in failed_files])
        return JSONResponse({"answer": message})

    # Combine readable OCR text for GPT
    all_text_str = "\n\n".join(readable_files)

    # Extract keywords for reference
    keywords_text = extract_keywords(all_text_str, top_n=150)
    log.info(f"Extracted keywords: {keywords_text[:500]}...")  

    documents_text = "\n".join(
        [f"{i+1}. File: {doc['filename']}\nContent:\n{doc['text']}" for i, doc in enumerate(all_text_list)]
    )

    # Use field extractor
    result = await extract_structured_fields(documents_text, question, keywords_text)
    
    return JSONResponse(result)


@router.post("/ocr/image", response_model=OCRResponse)
async def ocr_image(file: UploadFile = File(...)):
    """
    Extract text from a single image file.
    """
    log.info(f"OCR image endpoint: {file.filename}")
    
    try:
        result = await extract_text(file)
        
        if isinstance(result, dict) and "success" in result:
            return OCRResponse(**result)
        else:
            # For non-image files that return string
            return OCRResponse(
                success=True,
                message="Text extracted successfully",
                text=result if isinstance(result, str) else ""
            )
    except Exception as e:
        log.error(f"OCR failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/pdf", response_model=OCRResponse)
async def ocr_pdf(file: UploadFile = File(...)):
    """
    Extract text from a PDF file.
    """
    log.info(f"OCR PDF endpoint: {file.filename}")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        result = await extract_text(file)
        
        return OCRResponse(
            success=True,
            message="Text extracted from PDF",
            text=result if isinstance(result, str) else result.get("text", "")
        )
    except Exception as e:
        log.error(f"PDF OCR failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/document", response_model=OCRResponse)
async def ocr_document(file: UploadFile = File(...)):
    """
    Extract text from any supported document format.
    Supports: images, PDFs, DOCX, Excel, CSV, TXT
    """
    log.info(f"OCR document endpoint: {file.filename}")
    
    try:
        result = await extract_text(file)
        
        if isinstance(result, dict) and "success" in result:
            return OCRResponse(**result)
        else:
            return OCRResponse(
                success=True,
                message="Text extracted successfully",
                text=result if isinstance(result, str) else ""
            )
    except Exception as e:
        log.error(f"Document OCR failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/video", response_model=OCRResponse)
async def ocr_video(file: UploadFile = File(...)):
    """
    Extract text from video frames.
    Supports: mp4, avi, mov, mkv
    """
    log.info(f"OCR video endpoint: {file.filename}")
    
    video_exts = ['mp4', 'avi', 'mov', 'mkv']
    if not any(file.filename.lower().endswith(ext) for ext in video_exts):
        raise HTTPException(status_code=400, detail="File must be a video (mp4, avi, mov, mkv)")
    
    try:
        result = await extract_text(file)
        
        return OCRResponse(
            success=True,
            message="Text extracted from video frames",
            text=result if isinstance(result, str) else result.get("text", "")
        )
    except Exception as e:
        log.error(f"Video OCR failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/fields", response_model=FieldExtractionResponse)
async def extract_fields(file: UploadFile = File(...), field_type: str = Form("auto")):
    """
    Extract structured fields from a document.
    
    Args:
        file: Document file
        field_type: Type of extraction - "invoice", "form", or "auto"
    """
    log.info(f"Field extraction endpoint: {file.filename}, type: {field_type}")
    
    try:
        # Extract text first
        text_result = await extract_text(file)
        text = text_result.get("text", "") if isinstance(text_result, dict) else text_result
        
        if not text:
            raise HTTPException(status_code=400, detail="No text could be extracted from file")
        
        # Extract fields based on type
        if field_type == "invoice":
            result = await extract_invoice_fields(text)
        elif field_type == "form":
            result = await extract_form_fields(text)
        else:
            # Auto-detect or use general extraction
            result = await extract_invoice_fields(text)
        
        return FieldExtractionResponse(
            success=True,
            fields=result
        )
    except Exception as e:
        log.error(f"Field extraction failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
