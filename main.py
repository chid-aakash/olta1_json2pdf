from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import io
# Remove reportlab imports if they are no longer directly used in this file
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.units import inch
import json
import os
import subprocess # New import
import tempfile   # New import

app = FastAPI()

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic model to expect a dictionary under the key "data"
class JsonPayload(BaseModel):
    data: Dict[str, Any]

@app.post("/convert_json_to_pdf/")
async def convert_json_to_pdf(payload: JsonPayload):
    """
    Accepts JSON data containing 'config_data_content' and 'details_data_content',
    triggers generate_itinerary.py to process it, and returns the generated PDF.
    """
    temp_config_file_path = None
    temp_details_file_path = None
    try:
        config_data_content = payload.data.get("config_data_content")
        details_data_content = payload.data.get("details_data_content")

        if not isinstance(config_data_content, dict) or not isinstance(details_data_content, dict):
            missing_keys = []
            if not isinstance(config_data_content, dict):
                missing_keys.append("'config_data_content' (as an object)")
            if not isinstance(details_data_content, dict):
                missing_keys.append("'details_data_content' (as an object)")
            raise HTTPException(status_code=400, detail=f"Payload must contain { ' and '.join(missing_keys) } within the 'data' object.")

        # Create temporary file for config data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_config_file:
            json.dump(config_data_content, tmp_config_file)
            temp_config_file_path = tmp_config_file.name

        # Create temporary file for details data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_details_file:
            json.dump(details_data_content, tmp_details_file)
            temp_details_file_path = tmp_details_file.name
        
        script_path = "generate_itinerary.py"
        os.makedirs("outputs", exist_ok=True)

        cmd = ["python3", script_path, temp_config_file_path, temp_details_file_path]
        
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if process.returncode != 0:
            error_message = f"generate_itinerary.py failed with exit code {process.returncode}.\nStderr: {process.stderr}\nStdout: {process.stdout}"
            print(error_message)
            raise HTTPException(status_code=500, detail=f"Error during PDF generation script: {process.stderr[:200]}")

        output_pdf_path = os.path.join("outputs", "itinerary_output.pdf")

        if not os.path.exists(output_pdf_path):
            error_message = f"PDF file not found at {output_pdf_path} after script execution.\nStderr: {process.stderr}\nStdout: {process.stdout}"
            print(error_message)
            raise HTTPException(status_code=500, detail="PDF file not found after script execution.")

        def file_iterator(file_path, chunk_size=8192):
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        return StreamingResponse(file_iterator(output_pdf_path), media_type="application/pdf",
                                 headers={"Content-Disposition": "attachment; filename=itinerary_output.pdf"})

    except HTTPException: 
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if temp_config_file_path and os.path.exists(temp_config_file_path):
            os.remove(temp_config_file_path)
        if temp_details_file_path and os.path.exists(temp_details_file_path):
            os.remove(temp_details_file_path)

if __name__ == "__main__":
    import uvicorn
    # To run this: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True) 