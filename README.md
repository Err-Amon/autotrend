# AutoTrend Video Factory

A desktop tool that automates short-form video creation end-to-end. It collects trending topics, generates a script using an LLM, converts it to voice narration using Google AI Studio Gemini TTS (with Piper TTS as an offline fallback), downloads matching stock clips, assembles a vertical video with synchronised subtitles, and uploads to YouTube Shorts, Instagram Reels, and Facebook Reels.

---

## Requirements

- Python 3.10 or higher
- Node.js 18 or higher
- FFmpeg installed and available in system PATH
- Piper TTS binary and voice model (used as fallback if Google TTS is not configured)

---

## Project Structure

```
autotrend/
├── .env
├── requirements.txt
├── package.json
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── api/routes.py
│   ├── pipelines/video_pipeline.py
│   ├── services/
│   ├── integrations/
│   ├── utils/
│   └── storage/
└── frontend/
    ├── electron/main.js
    ├── electron/preload.js
    ├── public/index.html
    ├── vite.config.js
    └── src/
```

---

## Setup

### 1. Clone and enter the project

```bash
cd autotrend
```

### 2. Install Python dependencies

```bash
uv add -r requirements.txt
```

### 3. Install Node dependencies

```bash
npm install
```

### 4. Install FFmpeg

Windows: Download from ffmpeg.org, extract, and add the bin folder to your system PATH.
Linux: `sudo apt install ffmpeg`
Mac: `brew install ffmpeg`

Verify: `ffmpeg -version`

### 5. Configure environment

Copy `.env.example` to `.env` and fill in your API keys. At minimum you need GOOGLE_AI_STUDIO_API_KEY and PEXELS_API_KEY to run the pipeline.

---

## Running the Project

Open two terminals.

Terminal 1 — start the backend:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Terminal 2 — start the frontend:

```bash
npm run dev
```

The Electron desktop window will open automatically once Vite is ready.

To run the frontend only in a browser (without Electron):

```bash
npm run dev:vite
```

Then open http://localhost:5173 in your browser.

---

## APIs and Resources

### OpenRouter (Qwen 3.6 Plus LLM — script generation, trend filtering, and visual keyword extraction)

Free/Paid API via OpenRouter.

1. Go to openrouter.ai
2. Sign in and create an API key
3. Copy the key into OPENROUTER_API_KEY in .env
4. Set OPENROUTER_MODEL=openrouter/qwen-3.6-plus in .env

Model used: qwen-3.6-plus

Qwen 3.6 Plus is used to analyse the generated script and extract visual search queries that are used to fetch relevant stock clips from Pexels and Pixabay.


### Google AI Studio (Gemini TTS — voice narration)

Free API. Used as the primary TTS engine.

1. Go to aistudio.google.com
2. Sign in with your Google account
3. Click "Get API key" and create a new key
4. Copy the key into GOOGLE_AI_STUDIO_API_KEY in .env
5. Set USE_GOOGLE_TTS=True in .env

Model used: gemini-2.5-flash-preview-tts

Available voices: Aoede, Charon, Fenrir, Kore, Puck (set via GOOGLE_TTS_VOICE in .env).

If USE_GOOGLE_TTS is False or the key is missing, the pipeline automatically falls back to Piper TTS.


### Piper TTS (offline voice generation — fallback)

Free and open source. Runs fully offline. No account or API key needed. Used when Google TTS is not configured or fails.

Binary: github.com/rhasspy/piper/releases
Voice model: huggingface.co/rhasspy/piper-voices under en/en_US/lessac/medium

Download both the .onnx model file and the .onnx.json config file and place them in the models/ directory inside the project root.

Set PIPER_EXECUTABLE and PIPER_MODEL_PATH in .env to point to the binary and model file.


### Pexels (stock video clips)

Free API with generous limits.

1. Go to pexels.com/api
2. Sign in or create an account
3. Your API key is shown on the dashboard immediately after signing in
4. Copy it into PEXELS_API_KEY in .env

The pipeline fetches clips using multiple visual search queries extracted from the script by Gemini, so the footage matches the actual topic of the video.


### Pixabay (stock video clips — fallback)

Free API, optional. Used when Pexels does not return enough clips.

1. Go to pixabay.com/api/docs
2. Sign in or create an account
3. Your API key is shown at the top of the documentation page
4. Copy it into PIXABAY_API_KEY in .env


### Google News RSS (trend collection)

No key or account required. The pipeline fetches Google News RSS feeds directly using niche-specific search queries. This works out of the box.


### YouTube RSS and HackerNews (trend collection)

No key or account required. YouTube channel RSS feeds and the HackerNews Algolia API are both fully public. These work out of the box.


### Google Trends via pytrends (trend collection)

No key required. pytrends uses the public Google Trends web interface. Works out of the box.


### YouTube Data API (upload to YouTube Shorts)

Free via Google Cloud. Requires one-time OAuth setup.

1. Go to console.cloud.google.com
2. Create a new project
3. Search for and enable the YouTube Data API v3
4. Go to Credentials and click Create Credentials, then OAuth 2.0 Client ID
5. Set the application type to Desktop App
6. Download the JSON file, rename it to client_secrets.json, and place it in the project root
7. Copy the client_id and client_secret values into YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env
8. On the first upload attempt, a browser window will open for one-time authorisation. After approving, a token.json file is saved automatically and used for all future uploads.


### Meta Graph API (upload to Facebook Reels)

Free. Requires a Facebook Developer account and a Facebook Page.

1. Go to developers.facebook.com and create an app with type Business
2. Add the Pages API product to your app
3. Go to Graph API Explorer, select your app, and generate a Page Access Token
4. Find your Page ID in your Facebook Page settings under About
5. Copy the token into FACEBOOK_ACCESS_TOKEN and the ID into FACEBOOK_PAGE_ID in .env


### Meta Graph API (upload to Instagram Reels)

Free. Requires a Professional Instagram account (Creator or Business) linked to a Facebook Page.

1. Your Instagram account must be set to Professional under account settings
2. Link the Instagram account to a Facebook Page
3. In the same Facebook Developer app, add the Instagram Graph API product
4. Open Graph API Explorer and generate a token with the following permissions: instagram_basic and instagram_content_publish
5. To find your Instagram User ID, call GET /me?fields=id in Graph API Explorer with that token and copy the returned id value
6. Copy the token into INSTAGRAM_ACCESS_TOKEN and the ID into INSTAGRAM_USER_ID in .env

Note: Instagram upload requires the final video to be hosted at a publicly accessible HTTPS URL. Pass this URL as video_public_url inside the upload_config when triggering a job via the API.


### FFmpeg (video assembly)

Free and open source. Required for all video processing.

ffmpeg.org — download for your platform.

---

## Minimum Required Keys

To generate a video without uploading, you only need:

- GOOGLE_AI_STUDIO_API_KEY
- PEXELS_API_KEY
- FFmpeg installed

All upload keys (YouTube, Facebook, Instagram) are optional and only needed if you want to publish the finished video automatically.

---

## Hardware

- RAM: 8GB minimum
- CPU: Any modern CPU (no GPU required)
- Disk: 1 to 2GB free for temporary media files during processing

---

## Tech Stack

| Layer | Tool |
|---|---|
| Desktop UI | React 18 + Electron 30 |
| Build tool | Vite 5 |
| Backend | Python + FastAPI |
| LLM | OpenRouter Qwen 3.6 Plus |
| Voice (primary) | Google AI Studio Gemini TTS (gemini-2.5-flash-preview-tts) |
| Voice (fallback) | Piper TTS (offline) |
| Trend sources | Google News RSS, YouTube RSS, HackerNews API, Google Trends |
| Stock video | Pexels API, Pixabay API |
| Video assembly | FFmpeg |
| Upload | YouTube Data API v3, Meta Graph API |
