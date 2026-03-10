# AutoTrend Video Factory

AI-powered desktop tool for fully automated short video creation and upload.

## Setup

### Backend
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd backend && uvicorn main:app --reload --port 8000
```

### Frontend
```bash
npm install
npm run dev
```

## Configuration
Fill in all values in `.env` before running.

## Pipeline
Trends → Niche Filter → Script → Voice → Clips → Assembly → Subtitles → Upload
