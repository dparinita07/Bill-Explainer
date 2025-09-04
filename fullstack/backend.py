from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import re
from deep_translator import GoogleTranslator
from transformers import pipeline

# ✅ FastAPI app
app = FastAPI()

# OPTIONAL: Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Hugging Face IBM Granite Token
HF_TOKEN = "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"

# Load IBM Granite
try:
    chatbot = pipeline(
        "text-generation",
        model="ibm-granite/granite-7b",
        trust_remote_code=True,
        use_auth_token=HF_TOKEN
    )
except Exception as e:
    chatbot = None
    print("⚠️ Could not load IBM Granite model:", e)

# --- Helper function ---
def extract_info(text: str):
    amount_match = re.search(r'(₹|Rs\.?)\s?(\d+[,.]?\d*)', text)
    due_date_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text)
    return {
        "type": "Electricity Bill",
        "amount_due": amount_match.group(0) if amount_match else "Not found",
        "due_date": due_date_match.group(0) if due_date_match else "Not found"
    }

# --- OCR Endpoint ---
@app.post("/ocr/")
async def ocr_bill(file: UploadFile):
    img = Image.open(file.file)
    text = pytesseract.image_to_string(img, lang="eng+tel")
    parsed_info = extract_info(text)
    translator = GoogleTranslator(source="auto", target="te")
    translated_text = translator.translate(text)
    translated_structured = {
        "బిల్లు రకం": translator.translate(parsed_info["type"]),
        "చెల్లించవలసిన మొత్తం": translator.translate(parsed_info["amount_due"]) if parsed_info["amount_due"] != "Not found" else "లభించలేదు",
        "చెల్లించవలసిన తేదీ": translator.translate(parsed_info["due_date"]) if parsed_info["due_date"] != "Not found" else "లభించలేదు"
    }
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
        return {"reply": "⚠️ IBM Granite model is not available."}
    response = chatbot(query, max_new_tokens=150, do_sample=True, temperature=0.7)
    return {"reply": response[0]["generated_text"]}