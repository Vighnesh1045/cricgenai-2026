# CricGenAI 2026

A Streamlit chat app for querying ICC Men's T20 World Cup 2026 data in natural language, powered by a LangChain SQL agent and NVIDIA NIM (Llama 3.3 70B).

## Setup

```bash
pip install -r requirements.txt
python database_setup.py   # builds t20_wc_2026.db from data/*.csv
streamlit run app.py
```

Provide an NVIDIA API key via the `NVIDIA_API_KEY` environment variable (e.g. in a `.env` file) or enter it in the sidebar at runtime.

## Notes

- `database_setup.py` rebuilds `t20_wc_2026.db` from the CSVs in `data/` on every run.
- The app opens the SQLite database in read-only mode before handing it to the SQL agent, so a question (including a prompt-injected one) can never modify or drop data.
