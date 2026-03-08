# Tibetan Learning Tutorial Generator

A web application that generates Tibetan language learning materials with word-by-word translations in Chinese and English, plus simple phonetic pronunciation guides.

## Features

- **Web UI** - Paste Tibetan text and generate interactive tutorials
- **Background Processing** - Progress tracking with real-time updates
- **GLM API Integration** - High-quality translations using Claude API
- **Buddhist Aesthetic** - Traditional styling with cream, burgundy, and gold colors
- **Self-contained HTML** - Download static HTML files for offline use
- **SQLite Persistence** - All jobs saved and accessible from homepage

## Quick Start

### Prerequisites

- Docker and Docker Compose
- GLM API token (Anthropic-compatible endpoint)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/xyshyniaphy/tibentan_learn.git
   cd tibentan_learn
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   # Edit .env and add your API token
   ```

3. Run with Docker:
   ```bash
   docker compose up --build
   ```

4. Open http://localhost:8340

## Usage

1. **Create Tutorial** - Click "New Tutorial" and paste Tibetan text
2. **Watch Progress** - Real-time progress bar shows translation status
3. **View Result** - Interactive HTML with four columns:
   - Tibetan (original script)
   - Phonetic (romanized pronunciation)
   - Chinese (translation)
   - English (translation)
4. **Download** - Get standalone HTML file for offline use

## Example Tibetan Text

```
བཀྲ་ཤིས་བདེ་ལེགས་ཞུ་བ་ཡིན། ཐུགས་རྗེ་ཆེ།
```
(Tashi delek su wa yin. Thuje che - Greetings and thank you)

## Project Structure

```
tibentan_learn/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings and environment
│   ├── database.py          # SQLite connection
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── pages.py         # HTML page routes
│   │   └── api.py           # REST API endpoints
│   ├── services/
│   │   ├── tibetan_parser.py   # Word extraction
│   │   ├── translator.py       # GLM API client
│   │   └── html_generator.py   # Output generation
│   └── templates/           # Jinja2 HTML templates
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage - list all jobs |
| `/input` | GET | Input form for Tibetan text |
| `/api/generate` | POST | Create new translation job |
| `/api/progress/{job_id}` | GET | Get job progress (JSON) |
| `/api/download/{job_id}` | GET | Download generated HTML |
| `/result/{job_id}` | GET | View generated tutorial |
| `/progress/{job_id}` | GET | Progress page with polling |

## Configuration

Environment variables (set in `.env` or `docker-compose.yml`):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_AUTH_TOKEN` | API authentication token | Required |
| `ANTHROPIC_BASE_URL` | API endpoint URL | `https://api.z.ai/api/anthropic` |

## Technology Stack

- **Backend:** FastAPI, SQLAlchemy, Uvicorn
- **Frontend:** Jinja2 templates, Vanilla JavaScript
- **Database:** SQLite
- **API:** HTTPX for async HTTP requests
- **Container:** Docker, Python 3.12-slim

## License

MIT
