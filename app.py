import streamlit as st
import os
import requests
from dotenv import load_dotenv
import PyPDF2
import io
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="PitchSpark 🚀",
    page_icon="⚡",
    layout="wide"
)

# --- Step 1: Load Environment Variables ---
load_dotenv()
github_pat = os.getenv("GITHUB_PAT")

if not github_pat:
    st.error("Error: GITHUB_PAT not found. Please add it in Streamlit Secrets.")
    st.stop()

# --- Step 2: GitHub API Settings ---
API_URL = "https://models.github.ai/inference/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {github_pat}",
    "Content-Type": "application/json"
}

# --- Step 3: Helper Functions ---

def extract_text_from_pdf(pdf_file):
    """Extracts text from an uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None


def get_spacy_suggestions(text):
    """Detect weak phrases using regex instead of Spacy."""
    text_lower = text.lower()
    suggestions = []

    weak_phrases = {
        "i think": "Try a more confident phrase.",
        "i believe": "Use a stronger, assertive tone.",
        "helped with": "Use stronger verbs like 'Assisted', 'Contributed', or 'Implemented'.",
        "responsible for": "Use action verbs like 'Managed', 'Led', or 'Owned'."
    }

    for phrase, advice in weak_phrases.items():
        if phrase in text_lower:
            suggestions.append(f"Found: '{phrase}'. {advice}")

    return suggestions


def get_ai_analysis(text_to_analyze, prompt):
    """Call the AI API."""
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None


def calculate_score(suggestions, text):
    """Scoring engine."""
    score = 50
    score -= len(suggestions) * 15

    if len(text) < 150:
        score -= 20
    elif len(text) > 500:
        score += 20

    for keyword in ["data", "software", "python"]:
        if keyword in text.lower():
            score += 10

    return max(0, min(100, score))

# --- Step 4: UI Layout ---

with st.sidebar:
    st.title("PitchSpark ⚡")
    st.subheader("Your AI Career Coach")
    st.write("Paste your text and click **Analyze** to see your score.")
    st.divider()

    st.subheader("Your Overall Score")
    score_placeholder = st.empty()
    score_placeholder.metric("Score", "0 / 100", "Run analysis")

st.title("The AI That Turns Your LinkedIn Into a Hire-Magnet")

tab1, tab2 = st.tabs(["LinkedIn Profile Analyzer", "PDF Resume Analyzer"])

# --- Tab 1 ---
with tab1:
    st.header("Analyze Your LinkedIn 'About' Section")
    profile_text = st.text_area("Paste your LinkedIn 'About' section here:", height=200)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analyze My Profile"):
            if profile_text:
                with st.spinner("Analyzing..."):
                    suggestions = get_spacy_suggestions(profile_text)
                    score = calculate_score(suggestions, profile_text)

                    score_placeholder.metric("Score", f"{score} / 100")

                    analysis_prompt = f"""
                    Act as an expert LinkedIn reviewer ('PitchSpark').
                    Analyze this 'About' section:
                    - Critique section
                    - Top 3 Action items
                    ---
                    {profile_text}
                    """

                    ai_response = get_ai_analysis(profile_text, analysis_prompt)

                    if ai_response:
                        st.subheader("Your AI-Powered Analysis ✨")
                        st.write(ai_response)

                    if suggestions:
                        st.subheader("💡 Keyword Suggestions")
                        for s in suggestions:
                            st.warning(s)
            else:
                st.error("Please paste your profile text.")

    with col2:
        if st.button("Rewrite My 'About' Section", type="primary"):
            if profile_text:
                with st.spinner("Creating rewrites..."):
                    rewrite_prompt = f"""
                    Rewrite this LinkedIn 'About' in 3 styles:
                    1. Concise & Punchy
                    2. Story-Driven
                    3. Keyword-Optimized
                    ---
                    {profile_text}
                    """
                    rewrites = get_ai_analysis(profile_text, rewrite_prompt)

                    if rewrites:
                        st.subheader("AI Rewrites ✨")
                        st.write(rewrites)
            else:
                st.error("Paste your text first.")

# --- Tab 2 ---
with tab2:
    st.header("Analyze Your PDF Resume")
    resume_file = st.file_uploader("Upload your resume (PDF only)", type="pdf")

    if resume_file:
        with st.spinner("Reading and analyzing your resume..."):
            text = extract_text_from_pdf(io.BytesIO(resume_file.read()))

            if text:
                suggestions = get_spacy_suggestions(text)
                score = calculate_score(suggestions, text)

                score_placeholder.metric("Score", f"{score} / 100")

                analysis_prompt = f"""
                Act as a resume reviewer.
                Provide:
                - Critique
                - Top 3 Action items
                ---
                {text}
                """

                result = get_ai_analysis(text, analysis_prompt)

                if result:
                    st.subheader("Resume Analysis ✨")
                    st.write(result)

                if suggestions:
                    st.subheader("Keyword Suggestions")
                    for s in suggestions:
                        st.warning(s)
