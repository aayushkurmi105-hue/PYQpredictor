import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import io
import random
from fpdf import FPDF
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Path to Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.title("📘 PYQ Predictor Pro (Smart Version)")

uploaded_file = st.file_uploader("Upload your Question Paper (CSV / PDF / Image)", 
                                 type=["csv", "pdf", "jpg", "jpeg", "png"])

# Predefined subject keywords
topic_keywords = {
    "Economics": ["demand", "supply", "inflation", "gdp", "economy", "market"],
    "Finance": ["investment", "bank", "capital", "interest", "equity", "debt"],
    "Marketing": ["consumer", "product", "brand", "advertising", "promotion"],
    "Law": ["contract", "legal", "law", "rights", "case", "court"],
    "Management": ["leadership", "strategy", "planning", "organization"],
    "Statistics": ["mean", "median", "probability", "regression", "correlation"],
}

def detect_topic(question):
    doc = nlp(question.lower())
    for topic, keywords in topic_keywords.items():
        if any(word in question.lower() for word in keywords):
            return topic
    return "General"

if uploaded_file is not None:
    text = ""

    # Handle CSV Upload
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        st.write("✅ CSV Loaded Successfully", df.head())
        text = " ".join(df['Question'].astype(str).tolist()) if 'Question' in df.columns else ""

    # Handle PDF Upload
    elif uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + " "

    # Handle Image Upload
    else:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)

    st.subheader("📄 Extracted Text")
    st.text_area("Here’s the extracted text from your paper:", text, height=200)

    if text:
        # Split into questions
        questions = [q.strip() + "?" for q in text.split("?") if len(q.strip()) > 5]

        # Assign topics
        topics_detected = [(q, detect_topic(q)) for q in questions]

        # Convert to DataFrame
        df_topics = pd.DataFrame(topics_detected, columns=["Question", "Topic"])

        # Weightage = how many times topic appeared
        weightage = df_topics["Topic"].value_counts().reset_index()
        weightage.columns = ["Topic", "Frequency"]

        st.subheader("📊 Topic Weightage Analysis")
        st.write(weightage)

        # Generate Assumed Paper
        st.subheader("📑 Assumed Paper")
        num_qs = st.slider("How many questions do you want?", 1, 10, 5)

        # Pick from most frequent topics first
        assumed_qs = []
        for topic in weightage["Topic"]:
            topic_qs = df_topics[df_topics["Topic"] == topic]["Question"].tolist()
            random.shuffle(topic_qs)
            assumed_qs.extend(topic_qs[:2])  # take 2 from each topic

        assumed_qs = assumed_qs[:num_qs]

        for i, q in enumerate(assumed_qs, 1):
            st.write(f"Q{i}: {q}")

        # Download PDF
        if st.button("Download Assumed Paper PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, "Assumed Paper", ln=True, align="C")
            for i, q in enumerate(assumed_qs, 1):
                pdf.multi_cell(0, 10, f"Q{i}: {q}")
            pdf_output = "assumed_paper.pdf"
            pdf.output(pdf_output)
            st.success("✅ PDF Generated! Check project folder.")
