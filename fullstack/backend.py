from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
from transformers import pipeline
from teseract import ocr_and_translate  # <-- your Tesseract function

# ✅ FastAPI app
app = FastAPI()

# Hugging Face IBM Granite Token
HF_TOKEN = "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"

# Load smaller IBM Granite model (350M)
try:
    chatbot = pipeline(
        "text-generation",
        model="ibm-granite/granite-350M",  # smaller model for faster response
        trust_remote_code=True,
        use_auth_token=HF_TOKEN
    )
except Exception as e:
    chatbot = None
    print("⚠ Could not load IBM Granite model:", e)

# --- OCR Endpoint ---
@app.post("/ocr/")
async def ocr_bill(file: UploadFile):
    img = Image.open(file.file)
    text, parsed_info, translated_text, translated_structured = ocr_and_translate(img)
    return JSONResponse(content={
        "ocr_text": text,
        "parsed_info": parsed_info,
        "translated_text": translated_text,
        "translated_structured": translated_structured
    })

# --- Chatbot Endpoint ---
@app.post("/chat/")
async def chat(query: str = Form(...)):
    if not chatbot:
        return {"reply": "⚠ IBM Granite model is not available."}
    response = chatbot(query, max_new_tokens=150, do_sample=True, temperature=0.7)
    return {"reply": response[0]["generated_text"]}
