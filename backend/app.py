from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .extraction.pdf_processor import PDFProcessor
from .utils.error_handler import handle_extraction_error
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Course Data Extractor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process_files(files: List[UploadFile] = File(...)):
    try:
        results = []
        processor = PDFProcessor()

        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                continue

            # Save uploaded file temporarily
            temp_path = Path("data/temp") / file.filename
            temp_path.parent.mkdir(exist_ok=True)
            
            content = await file.read()
            temp_path.write_bytes(content)

            # Process PDF
            output_text = processor.process(temp_path)
            
            # Save extracted text
            output_path = Path("data/individual") / f"{file.filename.replace('.pdf', '.txt')}"
            output_path.write_text(output_text, encoding='utf-8')

            results.append({
                "filename": file.filename,
                "output_path": str(output_path),
                "status": "success"
            })

            # Cleanup
            temp_path.unlink(missing_ok=True)

        return {"status": "success", "results": results}

    except Exception as e:
        error_details = handle_extraction_error(e)
        raise HTTPException(status_code=500, detail=error_details)