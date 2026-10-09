# CricGenAI 2026

Ask questions about the ICC Men's T20 World Cup 2026 in **English, Hindi or Marathi** and get answers straight from a SQL database, with no SQL knowledge needed. Built as my M.Sc. research project.

Stack: Streamlit · LangChain SQL agent · NVIDIA NIM (Llama 3.3 70B) · SQLite

## Problem

Tournament statistics sit in tables, but most cricket fans think and ask in their own language, not in SQL. A plain chatbot hallucinates scores; a plain database needs a query language. CricGenAI lets the LLM write and run the SQL, then explains the result in the language the user picked, so every answer comes from the data rather than from the model's memory.

## How it works

```
 Streamlit chat UI ── language picker (English / Hindi / Marathi)
        │
        ▼
 Prompt builder ── question + selected language + table guide
        │           ("think in English, answer in <language>")
        ▼
 LangChain SQL agent (tool-calling, Llama 3.3 70B via NVIDIA NIM)
        │   inspects schema → writes SQL → runs it → reads the rows
        │   limits: 10 iterations, 60 s per question
        ▼
 SQLAlchemy engine ── SQLite opened mode=ro, 9-table allowlist
        │
        ▼
 Answer rendered in the user's language
```

- **One agent, one database.** The agent reasons in English (more reliable SQL generation) and is instructed to answer in the selected language.
- **9-table schema**, rebuilt from `data/*.csv` by `database_setup.py`: `matches` (55 rows), `key_scorecards`, `batting_stats`, `bowling_stats`, `awards`, `points_table`, `squads` (300 players), `venues`, `tournament_summary`. Indexes on `key_scorecards(player, match)` and `awards(match)`.
- **A table guide in the prompt** tells the agent which table answers which kind of question (for example, `awards` only for tournament-wide awards).

### Safety

The agent runs untrusted natural language through an LLM that writes SQL, so the database is locked down at the connection, not just in the prompt:

- SQLite is opened **read-only** (`mode=ro`). Even a prompt-injected "DROP TABLE" cannot execute.
- The agent only sees an **allowlist of the 9 tables**, so unrelated data is never exposed to it.
- Execution is bounded (`max_iterations=10`, `max_execution_time=60`).

## Example queries

The same question works in all three languages. Expected answers below were computed directly from `t20_wc_2026.db` with plain SQL.

| Language | Question | Expected answer |
|---|---|---|
| English | Which stadium hosted Semi-Final 1 and who won Player of the Match there? | Eden Gardens; Finn Allen |
| Hindi | सेमीफाइनल 1 किस स्टेडियम में खेला गया और वहां 'प्लेयर ऑफ द मैच' किसने जीता? | Eden Gardens; Finn Allen |
| Marathi | सेमीफायनल १ कोणत्या स्टेडियमवर खेळला गेला आणि तिथे 'प्लेअर ऑफ द मॅच' कोण ठरला? | Eden Gardens; Finn Allen |
| English | Who scored the fastest century in the 2026 World Cup and how many balls did it take? | Finn Allen, 33 balls |
| Hindi | 2026 विश्व कप में सबसे तेज़ शतक किसने लगाया? | Finn Allen, 33 balls |
| Marathi | २०२६ च्या विश्वचषकात सर्वात वेगवान शतक कोणी झळकावले? | Finn Allen, 33 balls |

The full set (15 questions: match deep dives, cross-table joins, tournament aggregates, bowling analysis, follow-ups) is in [`question_set.txt`](question_set.txt).

## Evaluation

[`eval_question_set.py`](eval_question_set.py) runs every question through the same agent configuration as the app and writes `eval_results.md` with each answer next to the expected tokens. Run it with your key:

```bash
NVIDIA_API_KEY=... python eval_question_set.py
```

**Results: not recorded yet.** The expected answers are verified against the database, but the end-to-end LLM run has not been committed. Once `eval_results.md` is generated it will be linked here with the pass count.

**Known limitation:** each question is sent to the agent on its own. The chat history on screen is not passed back to the model, so follow-ups that rely on "he" / "त्याने" / "उसने" (category 5 in the question set) are not resolved yet.

## Run locally

```bash
pip install -r requirements.txt
python database_setup.py   # builds t20_wc_2026.db from data/*.csv
streamlit run app.py
```

Provide an NVIDIA API key via the `NVIDIA_API_KEY` environment variable (for example in a `.env` file) or enter it in the sidebar at runtime.

## Tests

```bash
pip install -r requirements-dev.txt && pytest tests/
```

2 tests, both passing: `database_setup.py` builds all 9 tables with non-empty rows, and the two indexes exist. The tests rebuild `t20_wc_2026.db`, so re-commit or discard the regenerated file after running them.

## Deploy (Streamlit Community Cloud)

This is a Python/Streamlit app, so it can't be served by GitHub Pages (which only hosts static files). To get a public URL:

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**, pick this repository and branch, and set the main file path to `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   NVIDIA_API_KEY = "your-key-here"
   ```
4. Deploy. `t20_wc_2026.db` is already committed to the repo, so the deployed app has data immediately. If you change the CSVs in `data/`, run `python database_setup.py` locally and commit the regenerated `.db` file before redeploying.
