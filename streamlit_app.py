
import html
import pickle
import re
import string
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_URL_RE = re.compile(r"http\S+|www\S+")
_HTML_RE = re.compile(r"<.*?>")
_NUM_RE = re.compile(r"\d+")
_SPACE_RE = re.compile(r"\s+")
_LATIN_RE = re.compile(r"[A-Za-z]")

ENGLISH_STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'ain', 'all', 'am', 'an', 'and', 'any', 'are', 'aren',
    "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can', 'couldn', "couldn't", 'd', 'did', 'didn', "didn't", 'do', 'does', 'doesn', "doesn't", 'doing', 'don',
    "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn', "hadn't", 'has', 'hasn',
    "hasn't", 'have', 'haven', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', 'hers',
    'herself', 'him', 'himself', 'his', 'how', 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', 'isn',
    "isn't", 'it', "it'd", "it'll", "it's", 'its', 'itself', 'just', 'll', 'm', 'ma', 'me', 'mightn', "mightn't",
    'more', 'most', 'mustn', "mustn't", 'my', 'myself', 'needn', "needn't", 'no', 'nor', 'not', 'now', 'o', 'of',
    'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 're', 's',
    'same', 'shan', "shan't", 'she', "she'd", "she'll", "she's", 'should', "should've", 'shouldn', "shouldn't",
    'so', 'some', 'such', 't', 'than', 'that', "that'll", 'the', 'their', 'theirs', 'them', 'themselves', 'then',
    'there', 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 've', 'very', 'was', 'wasn', "wasn't", 'we', "we'd", "we'll", "we're", "we've",
    'were', 'weren', "weren't", 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with',
    'won', "won't", 'wouldn', "wouldn't", 'y', 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours',
    'yourself', 'yourselves',
}

URDU_STOPWORDS = {
    'اور','کے','کی','کا','میں','ہے','ہیں','کو','نے','سے','پر','یہ','وہ','ان','اس','جو','بھی','ہو','تھا','تھی',
    'تھے','گا','گی','گے','لیے','تک','لئے','ہی','جب','تو','اگر','مگر','لیکن','یا','نہیں','نہ','کہ','جس','اب',
    'پھر','کیا','ایک','ہر','سب','ہم','آپ','ساتھ','رہا','رہی','رہے','دیا','دی','ہوا','ہوئی','ہوئے','کر','کرنا',
    'کرتا','کرتی','کرتے','ہوتا','ہوتی','ہوتے'
}

DISPLAY_LABELS = {
    'Light': '🌞 Light',
    'Dark': '🌙 Dark',
}
_DISPLAY_LABELS_REVERSE = {label: key for key, label in DISPLAY_LABELS.items()}

_URDU_PUNCT_RE = re.compile(r'[،؟؛۔٪!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]')
_DIACRITIC_RE = re.compile(r'[\u064B-\u065F]')
_DIGIT_RE = re.compile(r'[0-9\u06F0-\u06F9\u0660-\u0669]')


def clean_english_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    text = text.lower()
    text = _URL_RE.sub(' ', text)
    text = _HTML_RE.sub(' ', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = _NUM_RE.sub(' ', text)
    text = _SPACE_RE.sub(' ', text).strip()
    words = [w for w in text.split() if w not in ENGLISH_STOPWORDS and len(w) > 1]
    return ' '.join(words)


def clean_urdu_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    text = (
        text.replace('ي', 'ی')
            .replace('ك', 'ک')
            .replace('ة', 'ہ')
            .replace('أ', 'ا')
            .replace('إ', 'ا')
            .replace('آ', 'ا')
    )
    text = _URL_RE.sub(' ', text)
    text = _DIACRITIC_RE.sub('', text)
    text = _URDU_PUNCT_RE.sub(' ', text)
    text = _DIGIT_RE.sub(' ', text)
    text = _LATIN_RE.sub(' ', text)
    text = _SPACE_RE.sub(' ', text).strip()
    words = [w for w in text.split() if w not in URDU_STOPWORDS and len(w) > 1]
    return ' '.join(words)


def detect_language(text: str) -> str:
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return 'urdu' if urdu_chars > 10 else 'english'


def get_trust_score(probability: float):
    score = int(round(float(probability) * 100))
    if score >= 80:
        category = 'Highly Trustworthy'
    elif score >= 60:
        category = 'Mostly Reliable'
    elif score >= 50:
        category = 'Uncertain - Likely Real'
    elif score >= 35:
        category = 'Suspicious'
    else:
        category = 'Potentially Misleading'
    return score, category


def is_gibberish(text: str, cleaned_text: str, threshold: float = 0.5):
    words = cleaned_text.split()
    if len(words) < 3:
        return True, 'Text too short after cleaning'
    for word in words:
        if len(word) >= 3 and len(set(word)) == 1:
            return True, 'Repeated-character pattern'
    avg_len = sum(len(w) for w in words) / len(words)
    if avg_len < 2.5:
        return True, 'Average word too short'
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total_chars = len([c for c in text if not c.isspace()])
    if total_chars > 0 and urdu_chars / total_chars < threshold:
        return True, 'Not enough Urdu script content'
    return False, ''


def load_models():
    base = Path(__file__).resolve().parent
    files = {
        'en_voting_model': base / 'models' / 'en_voting_model.pkl',
        'en_tfidf_vectorizer': base / 'models' / 'en_tfidf_vectorizer.pkl',
        'ur_voting_model': base / 'models' / 'ur_voting_model.pkl',
        'ur_tfidf_vectorizer': base / 'models' / 'ur_tfidf_vectorizer.pkl',
    }
    loaded = {}
    for key, path in files.items():
        if not path.exists():
            raise FileNotFoundError(f'Missing model file: {path}')
        with open(path, 'rb') as f:
            loaded[key] = pickle.load(f)
    return loaded


@st.cache_resource
def cached_models():
    return load_models()


def predict_text(text: str, language: str, loaded):
    cleaned = clean_urdu_text(text) if language == 'urdu' else clean_english_text(text)
    if language == 'urdu':
        gibberish, reason = is_gibberish(text, cleaned)
        if gibberish:
            return {
                'Language': language,
                'Prediction': 'Rejected',
                'Confidence': 0.0,
                'Trust Score': 0,
                'Category': 'Invalid Urdu input',
                'Reason': reason,
                'Cleaned Text': cleaned,
            }
        model = loaded['ur_voting_model']
        vectorizer = loaded['ur_tfidf_vectorizer']
    else:
        model = loaded['en_voting_model']
        vectorizer = loaded['en_tfidf_vectorizer']

    vec = vectorizer.transform([cleaned])
    pred = model.predict(vec)[0]
    prob = float(model.predict_proba(vec)[0][1])
    score, category = get_trust_score(prob)
    return {
        'Language': language,
        'Prediction': 'Real' if pred == 1 else 'Fake',
        'Confidence': round(prob, 4),
        'Trust Score': score,
        'Category': category,
        'Cleaned Text': cleaned,
    }


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

_BASE_CSS = """
.block-container {
    padding: 2rem 2rem 2rem 2rem;
    border-radius: 20px;
}

/* Text typed into the textarea stays white in BOTH themes (explicit, high
   specificity + !important so no per-theme rule can override it). */
.stTextArea textarea {
    color: #ffffff !important;
}

.stButton>button {
    background: #2563eb;
    color: white;
    border-radius: 12px;
    padding: 0.78rem 1.15rem;
    font-size: 1rem;
    border: none;
    min-width: 100%;
}
.stButton>button:hover { background: #1d4ed8; }
.stTextArea>div>div>textarea {
    border-radius: 16px;
    min-height: 240px;
}
.stSelectbox>div>div>div>div {
    border-radius: 14px;
}

/* Hamburger menu button pinned to the exact top-right corner of the viewport */
div.st-key-kebab_container {
    position: fixed;
    top: 0.9rem;
    right: 1.3rem;
    z-index: 10000;
    width: auto;
}
div.st-key-kebab_container button {
    width: 2.8rem;
    height: 2.8rem;
    min-width: 2.8rem;
    border-radius: 50%;
    font-size: 1.15rem;
    padding: 0;
    line-height: 1;
}

/* Dropdown menu panel, anchored just below the hamburger button */
div.st-key-display_menu {
    position: fixed;
    top: 4rem;
    right: 1.3rem;
    z-index: 10000;
    width: 200px;
}
.menu-panel {
    background: #6b6b6b;
    color: white;
    border-radius: 10px 10px 0 0;
    padding: 10px 12px 4px 12px;
    border: 1px solid #8a8a8a;
    box-shadow: 0 6px 20px rgba(0,0,0,.4);
    width:200px;
}
.menu-panel p { margin: 0; color: #e2e8f0; }

div.st-key-display_menu div[role="radiogroup"] {
    width: 100% !important;
    box-sizing: border-box;
    padding: 8px 12px;
    background: #6b6b6b;
    border: 1px solid #8a8a8a;
    border-top: none;
    border-radius: 0 0 10px 10px;
    width: 200px !important;
}

div.st-key-display_menu div[role="radiogroup"] * {
    color: #f1f5f9 !important;
}

.result-card {
    border: 2px solid transparent;
    border-radius: 18px;
    padding: 1.3rem;
    box-shadow: 0 14px 40px rgba(0,0,0,0.16);
    margin-bottom: 1rem;
}
.result-card.success { border-color: #22c55e; }
.result-card.danger { border-color: #ef4444; }
.result-card.warning { border-color: #f59e0b; }
.result-card .result-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 0.6rem; }
.result-card .result-meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
.result-card .result-meta div { padding: 0.9rem; border-radius: 14px; }
.result-card .result-meta label { display: block; font-size: 0.9rem; margin-bottom: 0.35rem; }
.result-card .result-meta strong { font-size: 1rem; }
.result-card details { margin-top: 0.5rem; }
.result-card summary {
    cursor: pointer;
    font-weight: 600;
    color: #60a5fa;
    padding: 0.4rem 0;
}
.result-card pre {
    white-space: pre-wrap;
    word-break: break-word;
    padding: 0.9rem;
    border-radius: 14px;
    margin-top: 0.5rem;
}

footer { visibility: hidden !important; }
header { visibility: hidden !important; }
a[href*="share" i], a[href*="deploy" i], button[aria-label*="share" i], button[aria-label*="deploy" i],
[data-testid*="share" i], [data-testid*="deploy" i], [class*="share" i], [class*="deploy" i] { display: none !important; }
[role="banner"] a, [role="banner"] button { display: none !important; }
"""

_DARK_COLORS = """
.stApp { background: linear-gradient(180deg, #0b1120 0%, #141a2f 45%, #1f2d4c 100%); color: #f8fafc; }
.block-container { background: rgba(10, 18, 34, 0.94); box-shadow: 0 20px 45px rgba(0, 0, 0, 0.35); }
.stTextArea>div>div>textarea { background: #101b34; }
.stSelectbox>div>div>div>div { background: #111b33; color: #e2e8f0; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p { color: #f8fafc; }
/* Widget labels ("Paste news text here", "Language mode") in dark mode */
.stTextArea label p, .stSelectbox label p { color: #f8fafc !important; }
.result-card { background: rgba(10, 18, 34, 0.92); }
.result-card .result-meta div { background: rgba(15, 23, 42, 0.8); color: #e2e8f0; }
.result-card .result-meta label { color: #94a3b8; }
.result-card pre { color: #e2e8f0; background: rgba(15, 23, 42, 0.95); }
"""

_LIGHT_COLORS = """
.stApp { background: linear-gradient(180deg, #eef2fb 0%, #e6ecf8 100%); color: #1e2a3a; }
.block-container { background: #f5f8fd; color: #1e2a3a; box-shadow: 0 10px 30px rgba(30,41,59,0.08); }
.stTextArea>div>div>textarea { background: #e9eef8; }
.stSelectbox>div>div>div>div { background: #e9eef8; color: #1e2a3a; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p { color: #1e2a3a; }
/* Widget labels ("Paste news text here", "Language mode") forced black in light mode */
.stTextArea label p, .stSelectbox label p { color: #000000 !important; }
.result-card { background: #eef2fb; box-shadow: 0 10px 30px rgba(30,41,59,0.08); }
.result-card .result-meta div { background: #e2e9f7; color: #1e2a3a; }
.result-card .result-meta label { color: #5b6b85; }
.result-card pre { color: #1e2a3a; background: #e2e9f7; }
"""


def inject_style(display_mode: str):
    theme_css = _LIGHT_COLORS if display_mode == 'Light' else _DARK_COLORS
    st.markdown(f"<style>{_BASE_CSS}\n{theme_css}</style>", unsafe_allow_html=True)


def render_result(result):
    if result['Prediction'] == 'Rejected':
        header_text = 'Input rejected'
        status_class = 'warning'
    else:
        header_text = f"Prediction: {result['Prediction']}"
        status_class = 'success' if result['Prediction'] == 'Real' else 'danger'

    cleaned = html.escape(result.get('Cleaned Text', ''))

    st.markdown(
        f"""
        <div class="result-card {status_class}">
            <div class="result-title">{header_text}</div>
            <div class="result-meta">
                <div><label>Language</label><strong>{html.escape(result['Language'].title())}</strong></div>
                <div><label>Confidence</label><strong>{result['Confidence'] * 100:.1f}%</strong></div>
                <div><label>Trust Score</label><strong>{result['Trust Score']}</strong></div>
                <div><label>Category</label><strong>{html.escape(result['Category'])}</strong></div>
            </div>
            <details>
                <summary>Show processed text</summary>
                <pre>{cleaned}</pre>
            </details>
        </div>
        """,
        unsafe_allow_html=True,
    )

    
    print_spacer_col, print_button_col = st.columns([4, 1])
    with print_button_col:
        print_clicked = st.button('🖨️ Print result', key='print_btn')

    if print_clicked:
        printable_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; padding: 24px; color: #1e2a3a; }}
            h2 {{ margin-top: 0; }}
            .row {{ margin-bottom: 10px; }}
            .row label {{ display: inline-block; width: 140px; color: #555; }}
            pre {{ white-space: pre-wrap; word-break: break-word; background: #f1f5f9; padding: 12px; border-radius: 8px; }}
        </style>
        </head>
        <body>
            <h2>{header_text}</h2>
            <div class="row"><label>Language:</label>{html.escape(result['Language'].title())}</div>
            <div class="row"><label>Confidence:</label>{result['Confidence'] * 100:.1f}%</div>
            <div class="row"><label>Trust Score:</label>{result['Trust Score']}</div>
            <div class="row"><label>Category:</label>{html.escape(result['Category'])}</div>
            <div class="row"><label>Processed text:</label></div>
            <pre>{cleaned}</pre>
            <script>
                window.onload = function() {{ window.print(); }};
            </script>
        </body>
        </html>
        """
        components.html(printable_html, height=0)


def main():
    st.set_page_config(
        page_title='Fake News Detection',
        page_icon='📰',
        layout='wide',
        initial_sidebar_state='collapsed',
    )

    if 'display_mode' not in st.session_state:
        st.session_state['display_mode'] = 'Dark'
    if 'menu_open' not in st.session_state:
        st.session_state['menu_open'] = False

    st.title('📰 Fake News Detection')
    st.markdown('Enter a news story in English or Urdu and press **Check News** to classify it.')


    with st.container(key="kebab_container"):
        if st.button("☰", key="kebab_btn"):
            st.session_state["menu_open"] = not st.session_state["menu_open"]

   
    with st.container(key="display_menu"):
        if st.session_state["menu_open"]:
            st.markdown('<div class="menu-panel"><p><b>Display</b></p></div>', unsafe_allow_html=True)
            display = st.radio(
                "",
                list(DISPLAY_LABELS.values()),
                index=list(DISPLAY_LABELS.values()).index(
                    DISPLAY_LABELS[st.session_state["display_mode"]]
                ),
                key="display_select",
                label_visibility="collapsed",
            )
            new_mode = _DISPLAY_LABELS_REVERSE[display]
            if new_mode != st.session_state["display_mode"]:
                
                st.session_state["display_mode"] = new_mode
                st.rerun()


    inject_style(st.session_state['display_mode'])

    mode = st.selectbox('Language mode', ['Auto detect', 'English only', 'Urdu only'])
    input_text = st.text_area('Paste news text here', height=260)

    spacer_col, button_col = st.columns([4, 1])
    with button_col:
        check_clicked = st.button('Check News', key='check_news')

    if 'last_result' not in st.session_state:
        st.session_state['last_result'] = None

    if check_clicked:
        if not input_text.strip():
            st.warning("Please paste a news story before checking it.")
        else:
            loaded = cached_models()

            if mode == "English only":
                language = "english"
            elif mode == "Urdu only":
                language = "urdu"
            else:
                language = detect_language(input_text)

            st.session_state['last_result'] = predict_text(input_text, language, loaded)

    if st.session_state['last_result'] is not None:
        render_result(st.session_state['last_result'])


if __name__ == '__main__':
    main()
