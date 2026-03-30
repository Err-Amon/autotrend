# AutoTrend Video Factory

AI-powered desktop tool for fully automated short video creation and upload.

## Features

- **Niche-based content**: Choose from multiple niches (Islamic History, Tech, Motivation, etc.)
- **Trend-driven**: Automatically fetches trending topics from Reddit, Google Trends
- **AI-powered scripts**: Uses Groq LLM to generate engaging short-form scripts
- **Automated video editing**: Fetches stock footage, adds voiceover, subtitles, and assembles final video
- **Multi-platform upload**: Supports YouTube, Facebook, Instagram
- **Desktop app**: Built with Electron for a native experience

### Backend
```bash
cd backend && uv run uvicorn main:app --reload --port 8000
```

### Frontend
```bash
npm run dev
```

## Configuration
Fill in all values in `.env` before running. At minimum, you need:
- `GROQ_API_KEY` - For AI script generation
- `PEXELS_API_KEY` - For stock video footage

## Pipeline
Trends → Niche Filter → Script → Voice → Clips → Assembly → Subtitles → Upload
