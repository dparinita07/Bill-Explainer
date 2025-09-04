import pytesseract
from PIL import Image
import re
import json
import os
from deep_translator import GoogleTranslator

# OPTIONAL: Set this to your Tesseract path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Step 1: Load bill image
IMAGE_PATH = 'bill.jpeg'  # Change if needed
if not os.path.exists(IMAGE_PATH):
    print(f"⚠️ Image file '{IMAGE_PATH}' not found.")
    exit()

img = Image.open(IMAGE_PATH)

# Step 2: OCR using Tesseract
text = pytesseract.image_to_string(img, lang='eng+tel')  # Try English and Telugu
print("\n🔍 OCR Extracted Text:\n", text)

# Step 3: Parse info using regex
def extract_info(text):
    amount_match = re.search(r'(₹|Rs\.?)\s?(\d+[,.]?\d*)', text)
    due_date_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text)

    return {
        "type": "Electricity Bill",  # You can customize this
        "amount_due": amount_match.group(0) if amount_match else "Not found",
        "due_date": due_date_match.group(0) if due_date_match else "Not found"
    }

parsed_info = extract_info(text)
print("\n🧠 Parsed Info:")
print(json.dumps(parsed_info, indent=2, ensure_ascii=False))

# Step 4: Translate full OCR text to Telugu using deep-translator
translated_text = GoogleTranslator(source='auto', target='te').translate(text)
print("\n🌐 Translated Text (Telugu):\n", translated_text)

# Step 5: Translate structured fields to Telugu
translator = GoogleTranslator(source='auto', target='te')

translated_structured = {
    "బిల్లు రకం": translator.translate(parsed_info["type"]),
    "చెల్లించవలసిన మొత్తం": (
        translator.translate(parsed_info["amount_due"]) if parsed_info["amount_due"] != "Not found" else "లభించలేదు"
    ),
    "చెల్లించవలసిన తేదీ": (
        translator.translate(parsed_info["due_date"]) if parsed_info["due_date"] != "Not found" else "లభించలేదు"
    )
}

print("\n🗂️ Structured Info in Telugu:")
print(json.dumps(translated_structured, indent=2, ensure_ascii=False))
