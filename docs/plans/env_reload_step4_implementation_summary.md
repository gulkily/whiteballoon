## Stage 1 – Override .env on load
- Changes: Updated env loader to call `load_dotenv(override=True)` so reloads apply the latest `.env` values.
- Verification: Not run (per project guidance). Manual check: edit `.env` (e.g., `SITE_TITLE`), wait for reload, refresh UI to confirm new value.
- Notes: Prioritizes `.env` over inherited environment values during dev reloads.
