# CricGenAI 2026

A Streamlit chat app for querying ICC Men's T20 World Cup 2026 data in natural language, powered by a LangChain SQL agent and NVIDIA NIM (Llama 3.3 70B).

## Run locally

```bash
pip install -r requirements.txt
python database_setup.py   # builds t20_wc_2026.db from data/*.csv
streamlit run app.py
```

Provide an NVIDIA API key via the `NVIDIA_API_KEY` environment variable (e.g. in a `.env` file) or enter it in the sidebar at runtime.

## Deploy (Streamlit Community Cloud)

This is a Python/Streamlit app, so it can't be served by GitHub Pages (which only hosts static files). To get a public URL:

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**, pick this repository and branch, and set the main file path to `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   NVIDIA_API_KEY = "your-key-here"
   ```
4. Deploy. `t20_wc_2026.db` is already committed to the repo, so the deployed app has data immediately. If you change the CSVs in `data/`, run `python database_setup.py` locally and commit the regenerated `.db` file before redeploying.

## Notes

- `database_setup.py` rebuilds `t20_wc_2026.db` from the CSVs in `data/` on every run.
- The app opens the SQLite database in read-only mode and restricts the SQL agent to a known table allowlist before handing it to the agent, so a question (including a prompt-injected one) can never modify, drop, or see unrelated data.
- Run tests with `pip install -r requirements-dev.txt && pytest tests/`.
