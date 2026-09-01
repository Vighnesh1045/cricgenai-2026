#app.py
import streamlit as st
import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Config 
st.set_page_config(page_title="CricGenAI 2026", page_icon="🏏", layout="wide")

# UI
st.markdown("""
    <style>
    .stApp { background-color: #f1f3f6; }
    .sports-banner {
        background-color: #009270;
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 0px 0px 15px 15px;
        margin-top: -60px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        border-bottom: 4px solid #00b388;
    }
    .sports-banner h1 { margin: 0; font-size: 28px; font-weight: 900; color: white; }
    .ticker {
        background-color: #ffffff;
        padding: 10px 20px;
        border-bottom: 1px solid #ddd;
        margin-bottom: 20px;
        font-size: 13px;
        font-weight: bold;
    }
    .live-dot { color: #d32f2f; animation: blink 1.5s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.3;} 100% {opacity: 1;} }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# Path Handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "t20_wc_2026.db")
db_url = f"sqlite:///{db_path.replace(os.sep, '/')}"

# Tables the agent is allowed to see/query, matching what database_setup.py loads.
ALLOWED_TABLES = [
    "awards", "batting_stats", "bowling_stats", "key_scorecards",
    "matches", "points_table", "squads", "tournament_summary", "venues",
]

# Sidebar 
with st.sidebar:
    st.markdown('### 🏆 CRICGENAI PANEL')
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/8/8d/Cricket_India_Crest.svg/1200px-Cricket_India_Crest.svg.png", width=70)
    user_lang = st.selectbox("🌐 LANGUAGE", ["English", "Marathi", "Hindi"])
    st.divider()
    api_key = os.getenv("NVIDIA_API_KEY") or st.text_input("🔑 NVIDIA API KEY", type="password")
    
    if os.path.exists(db_path):
        st.success("DATABASE CONNECTED")
    else:
        st.error("DATABASE MISSING")

# UI Header
st.markdown("""
    <div class="sports-banner">
        <p>ICC MEN'S T20 WORLD CUP</p>
        <h1>CricGenAI <span style="color:#00b388;">ANALYTICS</span></h1>
    </div>
    <div class="ticker">
        <span class="live-dot">●</span> LIVE DATA ACCESS | SERIES: 2026 WORLD CUP | ENGINE: NVIDIA NIM
    </div>
    """, unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("TOURNAMENT", "T20 WORLD CUP", "2026")
m2.metric("RECORDS", "9 DATASETS", "SQLITE")
m3.metric("INTELLIGENCE", "LLAMA 3.3", "NVIDIA")

if not api_key:
    st.warning("Please provide an NVIDIA API Key to start.")
    st.stop()

# DB & LLM Setup
@st.cache_resource
def init_db_and_llm(key, _url):
    # Open the SQLite file read-only so the agent can never modify/drop data,
    # even if a prompt-injected question asks it to.
    ro_url = _url.replace("sqlite:///", "sqlite:///file:", 1) + "?mode=ro&uri=true"
    engine = create_engine(ro_url)
    db = SQLDatabase(engine, include_tables=ALLOWED_TABLES, sample_rows_in_table_info=1)
    llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", api_key=key, temperature=0.1)
    return db, llm

if not os.path.exists(db_path):
    st.error("Database file not found. Run `python database_setup.py` first.")
    st.stop()

try:
    db, llm = init_db_and_llm(api_key, db_url)
except Exception as e:
    st.error(f"Failed to connect to database or LLM: {e}")
    st.stop()

agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="tool-calling",
    verbose=True,
    max_iterations=10,
    max_execution_time=60,
    handle_parsing_errors=True,
)

# Chat Logic
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome to the 2026 Analysis Desk. How can I help you today?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ask a question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.write(user_input)

    with st.chat_message("assistant"):
        final_prompt = f"""
        Language: {user_lang}
        Question: {user_input}
        
        TABLE GUIDE:
        1. 'matches': Use for winner, venue, scores, and 'player_of_the_match'.
        2. 'awards': ONLY for tournament-wide awards (e.g., Player of the Tournament).
        3. 'key_scorecards': Use for specific batting scores (runs, balls, fours).
        4. 'batting_stats' / 'bowling_stats': For overall tournament leaderboards.
        
        Rules: Think in English. Response must be in {user_lang}.
        """
        try:
            with st.spinner("Analyzing..."):
                response = agent_executor.invoke({"input": final_prompt})
                st.write(response["output"])
                st.session_state.messages.append({"role": "assistant", "content": response["output"]})
        except Exception as e:
            st.error(f"Error: {e}")