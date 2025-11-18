import streamlit as st
import os
import requests
from dotenv import load_dotenv
import PyPDF2
import io
import spacy
from spacy.matcher import Matcher

# --- Page Configuration ---
st.set_page_config(
    page_title="PitchSpark 🚀",
    page_icon="⚡",
    layout="wide"
)

# --- Step 1: Load Environment Variables & Spacy Model ---
load_dotenv()
github_pat = os.getenv("GITHUB_PAT")

if not github_pat:
    st.error("Error: GITHUB_PAT not found. Please check your .env file.")
    st.stop()

@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except:
        st.error("Error: Spacy model 'en_core_web_sm' not found.")
        st.error("Please run: python -m spacy download en_core_web_sm")
        st.stop()

nlp = load_spacy_model()

# --- Step 2: Define the GitHub API settings ---
API_URL = "https://models.github.ai/inference/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {github_pat}",
    "Content-Type": "application/json"
}

# --- Step 3: Define Helper Functions ---

def extract_text_from_pdf(pdf_file):
    """Extracts all text from an uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

def get_spacy_suggestions(text):
    """Analyzes text with Spacy for weak phrases."""
    doc = nlp(text)
    matcher = Matcher(nlp.vocab)
    patterns = [
        [{'LOWER': 'i'}, {'LOWER': 'think'}],
        [{'LOWER': 'i'}, {'LOWER': 'believe'}],
        [{'LOWER': 'helped'}, {'LEMMA': 'with'}],
        [{'LOWER': 'responsible'}, {'LOWER': 'for'}]
    ]
    matcher.add('WEAK_PHRASE', patterns)
    matches = matcher(doc)
    suggestions = []
    for match_id, start, end in matches:
        span = doc[start:end]
        suggestion = ""
        if span.text.lower() in ("i think", "i believe"):
            suggestion = f"Found: '{span.text}'. Try a more confident phrase."
        elif span.text.lower().startswith("helped"):
            suggestion = f"Found: '{span.text}'. Try a stronger action verb like 'Assisted', 'Supported', or 'Contributed to'."
        elif span.text.lower() == "responsible for":
            suggestion = f"Found: '{span.text}'. Try using strong action verbs like 'Managed', 'Owned', or 'Led'."
        if suggestion and suggestion not in suggestions:
            suggestions.append(suggestion)
    return suggestions

def get_ai_analysis(text_to_analyze, prompt):
    """Generic function to call the AI with a specific prompt."""
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
        ai_message = response_data["choices"][0]["message"]["content"]
        return ai_message
    except requests.exceptions.HTTPError as e:
        st.error(f"An API error occurred: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def calculate_score(spacy_suggestions, text):
    """Calculates a score based on your 'PitchSpark' brief."""
    score = 50
    score -= len(spacy_suggestions) * 15
    if len(text) < 150:
        score -= 20
    elif len(text) > 500:
        score += 20
    
    # Check for keywords
    if "data" in text.lower() or "software" in text.lower() or "python" in text.lower():
        score += 10
    
    # Clamp score between 0 and 100
    return max(0, min(100, score))

# --- Step 4: Define the "PitchSpark" Interface ---

# --- Sidebar (Your "Sticky Left Column") ---
with st.sidebar:
    st.title("PitchSpark ⚡")
    st.subheader("Your AI Career Coach")
    st.write("Welcome! Paste your text in a tab and click 'Analyze' to see your score.")
    st.divider()
    st.subheader("Your Overall Score")
    # We use a placeholder to update the score from the main page
    score_placeholder = st.empty()
    score_placeholder.metric("Score", "0 / 100", "Run analysis")
    st.write("This score is a composite of:\n- **Discoverability:** Keywords\n- **Content Quality:** Clarity & weak phrases\n- **Personal Brand:** Cohesion & length")

# --- Main Page Layout ---
st.title("The AI That Turns Your LinkedIn Into a Hire-Magnet")

tab1, tab2 = st.tabs(["LinkedIn Profile Analyzer", "PDF Resume Analyzer"])

# --- Tab 1: LinkedIn Analyzer ---
with tab1:
    st.header("Analyze Your LinkedIn 'About' Section")
    profile_text = st.text_area("Paste your LinkedIn 'About' section here:", key="linkedin_text", height=200)

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Analyze My Profile", key="linkedin_button"):
            if profile_text:
                with st.spinner("Analyzing..."):
                    spacy_suggestions = get_spacy_suggestions(profile_text)
                    score = calculate_score(spacy_suggestions, profile_text)
                    
                    # Update score in sidebar
                    score_placeholder.metric("Score", f"{score} / 100", f"{100-score} pts to improve" if score < 100 else "Perfect!")
                    
                    analysis_prompt = f"""
                    Act as an expert LinkedIn reviewer ('PitchSpark').
                    Analyze this 'About' section:
                    1.  A "Critique" section: What is strong, what's weak.
                    2.  A "Top 3 Action Items" section: Bullets on how to improve.
                    ---
                    {profile_text}
                    """
                    ai_analysis = get_ai_analysis(profile_text, analysis_prompt)
                    
                    if ai_analysis:
                        st.subheader("Your AI-Powered Analysis ✨")
                        st.write(ai_analysis)
                    
                    if spacy_suggestions:
                        st.subheader("💡 Keyword Suggestions")
                        for suggestion in spacy_suggestions:
                            st.warning(suggestion)
            else:
                st.error("Please paste your profile text into the box above.")
    
    with col2:
        # --- "One-Click AI Rewrites" (from your brief) ---
        if st.button("Rewrite My 'About' Section", key="linkedin_rewrite", type="primary"):
            if profile_text:
                with st.spinner("Generating 3 new versions..."):
                    rewrite_prompt = f"""
                    Act as 'PitchSpark,' an expert brand copywriter.
                    Rewrite the following LinkedIn 'About' section in 3 distinct styles:
                    1.  **Concise & Punchy:** Short, professional, and direct.
                    2.  **Story-Driven:** A compelling narrative.
                    3.  **Keyword-Optimized:** Focused on technical keywords for recruiters.
                    
                    Format the output clearly with Markdown headings for each style.
                    ---
                    {profile_text}
                    """
                    rewrites = get_ai_analysis(profile_text, rewrite_prompt)
                    
                    if rewrites:
                        st.subheader("AI-Powered Rewrites ✍️")
                        st.write(rewrites)
            else:
                st.error("Paste your 'About' text in the box to get rewrites.")

# --- Tab 2: Resume Analyzer ---
with tab2:
    st.header("Analyze Your PDF Resume")
    resume_file = st.file_uploader("Upload your resume in PDF format", type="pdf", key="resume_file")

    if resume_file:
        with st.spinner("Reading PDF and analyzing..."):
            resume_text = extract_text_from_pdf(io.BytesIO(resume_file.read()))
            
            if resume_text:
                spacy_suggestions = get_spacy_suggestions(resume_text)
                score = calculate_score(spacy_suggestions, resume_text)
                
                # Update score in sidebar
                score_placeholder.metric("Score", f"{score} / 100", f"{100-score} pts to improve" if score < 100 else "Perfect!")
                
                analysis_prompt = f"""
                Act as an expert Resume reviewer ('PitchSpark').
                Analyze this resume text:
                1.  A "Critique" section: What is strong, what's weak (e.g., action verbs, metrics).
                2.  A "Top 3 Action Items" section: Bullets on how to improve.
                ---
                {resume_text}
                """
                ai_analysis = get_ai_analysis(resume_text, analysis_prompt)
                
                if ai_analysis:
                    st.subheader("Your Resume Analysis ✨")
                    st.write(ai_analysis)
                
                if spacy_suggestions:
                    st.subheader("💡 Keyword Suggestions")
                    for suggestion in spacy_suggestions:
                        st.warning(suggestion)