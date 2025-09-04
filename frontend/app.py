import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
import re
import json
from deep_translator import GoogleTranslator
from transformers import pipeline
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

# -------------------------
# --- FastAPI Backend ---
# -------------------------
app = FastAPI()

# OPTIONAL: Set Tesseract path if on Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# IBM Granite HuggingFace token
HF_TOKEN = "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"  # Replace with your token

# Load IBM Granite model
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

# Helper to extract info from bills
def extract_info(text: str):
    amount_match = re.search(r'(₹|Rs\.?)\s?(\d+[,.]?\d*)', text)
    due_date_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text)
    return {
        "type": "Electricity Bill",
        "amount_due": amount_match.group(0) if amount_match else "Not found",
        "due_date": due_date_match.group(0) if due_date_match else "Not found"
    }

# OCR Endpoint
@app.post("/ocr/")
async def ocr_bill(file: UploadFile):
    img = Image.open(file.file)
    text = pytesseract.image_to_string(img, lang="eng+tel")
    parsed_info = extract_info(text)
    translator = GoogleTranslator(source="auto", target="te")
    translated_text = translator.translate(text)
    translated_structured = {
        "బిల్లు రకం": translator.translate(parsed_info["type"]),
        "చెల్లించవలసిన మొత్తం": (
            translator.translate(parsed_info["amount_due"]) if parsed_info["amount_due"] != "Not found" else "లభించలేదు"
        ),
        "చెల్లించవలసిన తేదీ": (
            translator.translate(parsed_info["due_date"]) if parsed_info["due_date"] != "Not found" else "లభించలేదు"
        )
    }
    return JSONResponse(content={
        "ocr_text": text,
        "parsed_info": parsed_info,
        "translated_text": translated_text,
        "translated_structured": translated_structured
    })

# Chatbot Endpoint
@app.post("/chat/")
async def chat(query: str = Form(...)):
    if not chatbot:
        return {"reply": "⚠️ IBM Granite model is not available."}
    response = chatbot(query, max_new_tokens=150, do_sample=True, temperature=0.7)
    return {"reply": response[0]["generated_text"]}


# -------------------------
# --- Streamlit Frontend ---
# -------------------------

# --- Translation Dictionary ---
translations = {
    "English": {
        "title": "📑 Local Language Bill Explainer",
        "upload": "Upload your bill",
        "chat": "💬 Ask Questions About Your Bill",
        "input": "Type your question here:",
        "speak": "🔊 Speak Response",
        "ai_reply": "This is a sample AI reply to your question: '{}'"
    },
    "हिंदी (Hindi)": {
        "title": "📑 स्थानीय भाषा बिल व्याख्याकार",
        "upload": "अपना बिल अपलोड करें",
        "chat": "💬 अपने बिल के बारे में प्रश्न पूछें",
        "input": "यहाँ अपना प्रश्न लिखें:",
        "speak": "🔊 उत्तर सुनें",
        "ai_reply": "यह आपका प्रश्न '{}' का उत्तर यहाँ है।"
    },
    "తెలుగు (Telugu)": {
        "title": "📑 స్థానిక భాష బిల్ వివరణ",
        "upload": "మీ బిల్‌ను అప్లోడ్ చేయండి",
        "chat": "💬 మీ బిల్ గురించి ప్రశ్నలు అడగండి",
        "input": "ఇక్కడ మీ ప్రశ్న టైప్ చేయండి:",
        "speak": "🔊 సమాధానం వినండి",
        "ai_reply": "మీ ప్రశ్న '{}' కు సమాధానం ఇక్కడ ఉంది."
    },
    "தமிழ் (Tamil)": {
        "title": "📑 உள்ளூர் மொழி பில் விளக்கம்",
        "upload": "உங்கள் பில் பதிவேற்றவும்",
        "chat": "💬 உங்கள் பில் பற்றி கேள்விகள் கேளுங்கள்",
        "input": "இங்கே உங்கள் கேள்வியை எழுதுங்கள்:",
        "speak": "🔊 பதிலை கேளுங்கள்",
        "ai_reply": "உங்கள் கேள்வி '{}' க்கு பதில் இங்கே உள்ளது."
    },
    "മലയാളം (Malayalam)": {
        "title": "📑 പ്രാദേശിക ഭാഷ ബിൽ വിശദീകരണം",
        "upload": "നിങ്ങളുടെ ബിൽ അപ്ലോഡ് ചെയ്യുക",
        "chat": "💬 നിങ്ങളുടെ ബിൽ സംബന്ധിച്ച് ചോദ്യങ്ങൾ ചോദിക്കുക",
        "input": "ഇവിടെ നിങ്ങളുടെ ചോദ്യമിടുക",
        "speak": "🔊 ഉത്തരം കേൾക്കുക",
        "ai_reply": "നിങ്ങളുടെ ചോദ്യം '{}' ന് മറുപടി ഇവിടെ കാണുന്നു."
    }
}

# --- Custom CSS ---
st.markdown(
    """
    <style>
        .main { background-color: #f9f9f9; }
        .upload-box {
            background: white; 
            padding: 20px; 
            border-radius: 15px;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.1); 
            text-align: center;
            color: black;
        }
        .chat-container {
            background: #2b2b2b; 
            border-radius: 15px; 
            padding: 15px;
            margin-top: 20px; 
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
            max-height: 400px; 
            overflow-y: auto;
            color: white;
        }
        .user-bubble {
            background-color: #1a73e8; 
            color: white; 
            padding: 10px; 
            border-radius: 10px;
            margin: 5px 0; 
            text-align: left;
        }
        .ai-bubble {
            background-color: #d1d1d1; 
            color: black; 
            padding: 10px; 
            border-radius: 10px;
            margin: 5px 0; 
            text-align: left;
        }
        input, textarea {
            color: black !important; 
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Language Selector ---
language = st.selectbox(
    "Choose your language",
    list(translations.keys())
)
ui = translations[language]

# --- Title ---
st.markdown(f"<h2 style='text-align:center;'>{ui['title']}</h2>", unsafe_allow_html=True)

# --- Upload Section ---
st.markdown('<div class="upload-box">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(ui["upload"], type=["png", "jpg", "jpeg", "pdf", "txt"])
st.markdown("</div>", unsafe_allow_html=True)

# --- File Preview ---
if uploaded_file:
    file_type = uploaded_file.type
    if "image" in file_type:
        image = Image.open(uploaded_file)
        st.image(image, caption=ui["upload"], use_column_width=True)
    elif "pdf" in file_type:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        if text.strip() == "":
            st.info("PDF uploaded but contains no extractable text.")
        else:
            st.text_area("Extracted PDF Text", text, height=200)
    elif "text" in file_type:
        content = uploaded_file.read().decode("utf-8")
        st.text_area("Bill Text", content, height=200)
    else:
        st.warning("Unsupported file type!")

# --- Chatbox ---
st.markdown(f"### {ui['chat']}")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
user_query = st.text_input(ui["input"])
if user_query:
    st.session_state.chat_history.append({"role": "user", "message": user_query})
    ai_response = ui["ai_reply"].format(user_query)
    st.session_state.chat_history.append({"role": "ai", "message": ai_response})

# --- Chat Display ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f'<div class="user-bubble">👤 You: {chat["message"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-bubble">🤖 AI: {chat["message"]}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- TTS Integration ---
def get_tts_model(language):
    if "Hindi" in language:
        return pipeline("text-to-speech", model="ai4bharat/indic-tts-hi")
    elif "తెలుగు" in language:
        return pipeline("text-to-speech", model="ai4bharat/indic-tts-te")
    elif "தமிழ்" in language:
        return pipeline("text-to-speech", model="ai4bharat/indic-tts-ta")
    elif "മലയാളം" in language:
        return pipeline("text-to-speech", model="ai4bharat/indic-tts-ml")
    else:
        return pipeline("text-to-speech", model="facebook/mms-tts-eng")

def speak_text(text, language):
    tts = get_tts_model(language)
    output = tts(text)
    audio_file = "output.wav"
    with open(audio_file, "wb") as f:
        f.write(output["audio"])
    return audio_file

if st.button(ui["speak"]):
    if st.session_state.chat_history:
        last_ai_message = st.session_state.chat_history[-1]["message"]
        audio_path = speak_text(last_ai_message, language)
        st.audio(audio_path, format="audio/wav")