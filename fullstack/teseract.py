import pytesseract
from PIL import Image
import re
from deep_translator import GoogleTranslator

# OPTIONAL: Set this to your Tesseract path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_and_translate(img: Image.Image):
    """
    Takes a PIL Image, performs OCR, parses bill info, 
    and translates both full text and structured fields to Telugu.
    Returns: text, parsed_info, translated_text, translated_structured
    """

    # Step 1: OCR using Tesseract
    text = pytesseract.image_to_string(img, lang='eng+tel')

    # Step 2: Parse info using regex
    def extract_info(text):
        amount_match = re.search(r'(₹|Rs\.?)\s?(\d+[,.]?\d*)', text)
        due_date_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text)
        return {
            "type": "Electricity Bill",
            "amount_due": amount_match.group(0) if amount_match else "Not found",
            "due_date": due_date_match.group(0) if due_date_match else "Not found"
        }

    parsed_info = extract_info(text)

    # Step 3: Translate full OCR text to Telugu
    translated_text = GoogleTranslator(source='auto', target='te').translate(text)

    # Step 4: Translate structured fields to Telugu
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

    # Step 5: Return everything
    return text, parsed_info, translated_text, translated_structured
