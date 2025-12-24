# PurpleDoc

Browser extension + local FastAPI backend that answers questions about the page you are viewing by scraping the URL, embedding chunks with Google Gemini, and generating responses in context.

## How it works
- Extension popup sends the active tab URL and your question to the backend at `http://127.0.0.1:8000/ask`.
- Backend scrapes the page, chunks and embeds text via Gemini, searches similar chunks with ChromaDB, and asks Gemini to answer using that context.
- Answers stream back to the popup via `chrome.storage` updates.

## Setup
1) Install Python deps: `pip install -r requirements.txt` (use a virtualenv(or conda) if you want).
2) This can be run as a `uv` project using the `pyproject.toml` file.
3) Add `.env` with `GOOGLE_API_KEY=your_key_here`.
4) Start backend: `./start.sh` (runs uvicorn on port 8000).
5) Load the extension:
   - Open `chrome://extensions`, enable Developer Mode.
   - Click “Load unpacked” and select the `extension` folder.
   - Pin the PurpleDoc icon and click it to open the popup.

## Design palette
- Primary: `#8a5cff` (accent), `#c08bff` (accent-2)
- Background gradient: dark purple/indigo
- Panel: `rgba(24, 18, 46, 0.92)`
- Text: `#f2edff`, Muted: `#b8acd8`
- Borders: `rgba(255, 255, 255, 0.08)`

## Icon
- Use any purple-themed chat/doc icon (64x64 or 128x128 PNG) placed at `extension/icon.png`.
- Update `extension/manifest.json` with `"icons": { "128": "icon.png" }` if you add it.

## Notes
- `MAX_CHUNKS` env var (default 8) limits how many chunks are embedded per request to keep responses fast.
- Open CORS is fine for local use but lock down origins if deploying beyond local. 
