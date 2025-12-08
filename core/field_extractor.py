# core/field_extractor.py
"""
Structured field extraction module for ImageAI.
Uses GPT to extract structured information from OCR text.

This module provides intelligent field extraction with:
- Invoice field extraction (invoice_number, date, total, items)
- Form field extraction with checkbox interpretation
- Custom question-based extraction
"""
from typing import Dict, Any, List, Optional
from utils.openai_client import getOpenai, call_openai_chat
from utils.file_handler import extract_keywords
from utils.logger import log


async def extract_structured_fields(text: str, question: str, keywords: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured fields from text using GPT based on a question.

    Args:
        text: OCR extracted text
        question: Question to ask about the text
        keywords: Optional pre-extracted keywords for context

    Returns:
        dict: {"answer": str, "confidence": float}
    """
    if not keywords:
        keywords = extract_keywords(text, top_n=150)
    
    # GPT prompt - enforce literal use of OCR text
    prompt = f"""
You are an AI assistant that extracts and structures information from document text.

The following is the full content extracted from uploaded documents (e.g., images, PDFs):
Documents:
{text}

Extracted keywords for reference: {keywords}

User question: {question}

Rules:
1. Use ONLY the text from the OCR/document.
2. If a question has checkboxes or multiple options (marked with 'x' for selected answers), interpret 'x' as the selected option.
3. Convert the selected option(s) into a natural, complete sentence answering the question.
4. Do NOT hallucinate, compute, or infer numbers.
5. Extract specific entities accurately and format as key-value pairs if applicable.
6. Preserve numbered lists or bullet points only if they are part of the answer.
7. If information is missing, respond: "Information not found in the documents."
8. Do not add information from outside sources.
9. Provide concise answers in **sentence form**, suitable for reading or reporting.
10. You are a text corrector for OCR outputs. If the OCR result contains spelling mistakes, grammatical errors, or misread characters (e.g., I1em instead of Item), infer and correct them to the most likely valid word or phrase, based on context. Always preserve the meaning and structure of the text.

Example:

OCR text:
15. Are you eligible to work in this country?
xYes
No

Output:
You are eligible to work in this country.

OCR text:
17. Employment type:
xFull-time
Part-time
Contract

Output:
The employment type is full-time.

OCR text:
18. Skills:
xPython
xJava
C++
JavaScript

Output:
The candidate has the following skills: Python and Java.
"""

    client = getOpenai()
    response = await call_openai_chat(
        client,
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You answer questions by extracting and structuring info from document content."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()

    # Clean up lines
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    clean_answer = "\n".join(lines)

    log.info(f"Answer generated: {clean_answer}")
    return {"answer": clean_answer}


async def extract_invoice_fields(text: str) -> Dict[str, Any]:
    """
    Extract invoice-specific fields from OCR text.

    Args:
        text: OCR extracted text from invoice

    Returns:
        dict: {
            "invoice_number": str,
            "date": str,
            "total": str,
            "items": List[dict],
            "vendor": str,
            "customer": str
        }
    """
    prompt = f"""
Extract the following fields from this invoice text:
- Invoice Number
- Date
- Total Amount
- Vendor/Seller Name
- Customer/Buyer Name
- Line Items (name, quantity, price)

Invoice Text:
{text}

Return the information in a structured format. If a field is not found, use "Not found".
"""

    client = getOpenai()
    response = await call_openai_chat(
        client,
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You extract structured invoice data from text."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()
    log.info(f"Invoice fields extracted: {answer}")
    
    return {"fields": answer}


async def extract_form_fields(text: str) -> Dict[str, Any]:
    """
    Extract form fields with checkbox interpretation.

    Args:
        text: OCR extracted text from form

    Returns:
        dict: Extracted form fields with checkbox values interpreted
    """
    prompt = f"""
Extract all form fields from this text. Pay special attention to:
- Checkboxes marked with 'x' or '☑' (interpret as selected)
- Radio buttons
- Text fields
- Dropdown selections

Form Text:
{text}

Return each field as: Field Name: Value
For checkboxes, convert to natural language (e.g., "Employment Type: Full-time" instead of "xFull-time")
"""

    client = getOpenai()
    response = await call_openai_chat(
        client,
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You extract form data and interpret checkboxes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()
    log.info(f"Form fields extracted: {answer}")
    
    return {"fields": answer}


def format_response(fields: Dict[str, Any]) -> str:
    """
    Format extracted fields as readable text.

    Args:
        fields: Dictionary of extracted fields

    Returns:
        str: Formatted text representation
    """
    if "answer" in fields:
        return fields["answer"]
    
    if "fields" in fields:
        return fields["fields"]
    
    # Generic formatting
    lines = []
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    
    return "\n".join(lines)
