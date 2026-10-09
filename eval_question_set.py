"""Run the question set against the SQL agent and write eval_results.md.

Usage: NVIDIA_API_KEY=... python eval_question_set.py

Each question is asked as a single-turn prompt, exactly as app.py sends it.
`expected` values were derived directly from t20_wc_2026.db with plain SQL.
The auto-check only matches Latin/ASCII tokens, so Hindi/Marathi answers that
transliterate names are marked REVIEW and need a manual read.
"""
import os
import sys

from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from sqlalchemy import create_engine

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "t20_wc_2026.db")
ALLOWED_TABLES = [
    "awards", "batting_stats", "bowling_stats", "key_scorecards",
    "matches", "points_table", "squads", "tournament_summary", "venues",
]

# (category, language, question, tokens that must appear in a correct answer)
QUESTIONS = [
    ("Match deep dive", "English", "Who scored the most runs for India in the Final and what was his strike rate?", ["Samson", "89"]),
    ("Match deep dive", "Marathi", "फायनलमध्ये भारतासाठी सर्वाधिक धावा कोणी केल्या आणि किती?", ["89"]),
    ("Match deep dive", "Hindi", "फाइनल मैच में भारत के लिए सबसे ज्यादा रन किसने बनाए?", ["89"]),
    ("Cross-table join", "English", "Which stadium hosted Semi-Final 1 and who won Player of the Match there?", ["Eden Gardens", "Finn Allen"]),
    ("Cross-table join", "Marathi", "सेमीफायनल १ कोणत्या स्टेडियमवर खेळला गेला आणि तिथे 'प्लेअर ऑफ द मॅच' कोण ठरला?", ["Eden Gardens"]),
    ("Cross-table join", "Hindi", "सेमीफाइनल 1 किस स्टेडियम में खेला गया और वहां 'प्लेयर ऑफ द मैच' किसने जीता?", ["Eden Gardens"]),
    ("Tournament aggregate", "English", "Who scored the fastest century in the 2026 World Cup and how many balls did it take?", ["Finn Allen", "33"]),
    ("Tournament aggregate", "Marathi", "२०२६ च्या विश्वचषकात सर्वात वेगवान शतक कोणी झळकावले?", ["33"]),
    ("Tournament aggregate", "Hindi", "2026 विश्व कप में सबसे तेज़ शतक किसने लगाया?", ["33"]),
    ("Bowling analysis", "English", "Which Indian bowlers took more than 10 wickets and what were their best figures?", ["Bumrah", "Chakravarthy", "14"]),
    ("Bowling analysis", "Marathi", "कोणत्या भारतीय गोलंदाजांनी स्पर्धेत १० पेक्षा जास्त बळी घेतले आणि त्यांची सर्वोत्तम कामगिरी काय होती?", ["14"]),
    ("Bowling analysis", "Hindi", "किन भारतीय गेंदबाजों ने 10 से अधिक विकेट लिए और उनका सर्वश्रेष्ठ प्रदर्शन क्या था?", ["14"]),
    ("Follow-up (single-turn)", "English", "How many total sixes did he hit in the tournament?", ["24"]),
    ("Follow-up (single-turn)", "Marathi", "त्याने संपूर्ण स्पर्धेत एकूण किती षटकार मारले?", ["24"]),
    ("Follow-up (single-turn)", "Hindi", "उसने पूरे टूर्नामेंट में कितने छक्के लगाए?", ["24"]),
]

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def build_agent(api_key):
    ro_url = f"sqlite:///file:{DB_PATH.replace(os.sep, '/')}?mode=ro&uri=true"
    db = SQLDatabase(create_engine(ro_url), include_tables=ALLOWED_TABLES, sample_rows_in_table_info=1)
    llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", api_key=api_key, temperature=0.1)
    return create_sql_agent(
        llm=llm, db=db, agent_type="tool-calling", verbose=False,
        max_iterations=10, max_execution_time=60, handle_parsing_errors=True,
    )


def build_prompt(language, question):
    return f"""
        Language: {language}
        Question: {question}

        TABLE GUIDE:
        1. 'matches': Use for winner, venue, scores, and 'player_of_the_match'.
        2. 'awards': ONLY for tournament-wide awards (e.g., Player of the Tournament).
        3. 'key_scorecards': Use for specific batting scores (runs, balls, fours).
        4. 'batting_stats' / 'bowling_stats': For overall tournament leaderboards.

        Rules: Think in English. Response must be in {language}.
        """


def main():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        sys.exit("Set NVIDIA_API_KEY to run the evaluation.")

    agent = build_agent(api_key)
    rows, passed = [], 0
    for category, language, question, tokens in QUESTIONS:
        try:
            answer = agent.invoke({"input": build_prompt(language, question)})["output"]
        except Exception as exc:  # record failures instead of aborting the run
            answer = f"ERROR: {exc}"
        normalized = answer.translate(DEVANAGARI_DIGITS).lower()
        ok = all(t.lower() in normalized for t in tokens)
        passed += ok
        rows.append((category, language, question, tokens, answer.replace("\n", " "), "PASS" if ok else "REVIEW"))
        print(f"[{rows[-1][5]}] {language}: {question[:60]}")

    with open(os.path.join(BASE_DIR, "eval_results.md"), "w", encoding="utf-8") as f:
        f.write(f"# Question set results\n\nAuto-matched {passed}/{len(QUESTIONS)}. REVIEW = needs a manual read.\n\n")
        f.write("| Category | Language | Question | Expected tokens | Agent answer | Auto |\n|---|---|---|---|---|---|\n")
        for category, language, question, tokens, answer, status in rows:
            f.write(f"| {category} | {language} | {question} | {', '.join(tokens)} | {answer} | {status} |\n")
    print(f"\nAuto-matched {passed}/{len(QUESTIONS)}; wrote eval_results.md")


if __name__ == "__main__":
    main()
