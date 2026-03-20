# Dark Pattern Detector

**AI-Driven Semantic Web Crawler for Detecting Deceptive Design Patterns**

A full-stack application that crawls websites using a real browser, detects deceptive UX patterns (dark patterns) using NLP and computer vision, and visualizes results in an interactive dashboard.

---

## Architecture

```
React Dashboard ──→ FastAPI REST API ──→ Redis Queue ──→ Celery Workers
                                                              │
                                                   ┌─────────┼─────────┐
                                                   │         │         │
                                              Selenium   spaCy    OpenCV
                                              Crawler    NLP      Vision
                                                   │         │         │
                                                   └─────────┼─────────┘
                                                              │
                                                        SQLite DB
```

## Features

- **Real-browser crawling** — Selenium with headless Chrome renders JavaScript-heavy pages
- **Priority-focused crawling** — Pages scored by semantic relevance are crawled first
- **NLP analysis** — spaCy tokenization/lemmatization + Sentence-BERT embeddings for topic relevance
- **Hybrid dark pattern detection** — Rule-based regex/keyword matching + DistilBERT ML classification
- **Visual analysis** — OpenCV screenshot analysis for urgency colors, modals, countdown timers, button asymmetry
- **Interactive graph** — React Flow visualization of site link structure with flagged nodes
- **Background processing** — Celery + Redis for non-blocking audit execution

## Detected Dark Pattern Types

| Pattern | Description |
|---------|-------------|
| Confirmshaming | Guilt-tripping the decline option |
| Urgency | False time pressure ("Act now!") |
| Scarcity | Fake low-stock warnings |
| Misdirection | Pre-selected checkboxes, hidden consent |
| Social Proof | Misleading popularity claims |
| Hidden Costs | Fees revealed late in checkout |
| Trick Questions | Confusing opt-in/opt-out language |
| Forced Continuity | Difficult subscription cancellation |
| Nagging | Repeated prompts after declining |

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Redis** server running on `localhost:6379`
- **Google Chrome** browser installed (for Selenium)

---

## Setup

### 1. Clone and install backend

```bash
cd project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_md
```

### 2. Start Redis

```bash
# macOS (Homebrew)
brew install redis && redis-server

# Ubuntu/Debian
sudo apt install redis-server && sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3. Install frontend

```bash
cd frontend
npm install
```

---

## Running

Open **three terminal windows**:

### Terminal 1 — FastAPI Backend

```bash
cd project
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 — Celery Worker

```bash
cd project
source venv/bin/activate
celery -A backend.tasks.celery_tasks worker --loglevel=info --concurrency=2
```

### Terminal 3 — React Frontend

```bash
cd project/frontend
npm start
```

The dashboard opens at **http://localhost:3000**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/start-audit` | Start a new audit (body: `{ url, topic, max_pages, threshold }`) |
| `GET` | `/api/audit-status/{task_id}` | Poll crawl progress |
| `GET` | `/api/results/{task_id}` | Full results (pages, patterns, screenshots, graph) |
| `GET` | `/api/patterns/{task_id}` | Detected dark patterns only |
| `GET` | `/api/screenshots/{task_id}` | Screenshot metadata |
| `GET` | `/api/graph/{task_id}` | React Flow-compatible graph data |

---

## Project Structure

```
project/
├── backend/
│   ├── main.py                          # FastAPI app entry point
│   ├── api/
│   │   └── routes.py                    # REST API endpoints
│   ├── crawler/
│   │   ├── crawler.py                   # Selenium-based web crawler
│   │   └── link_extractor.py            # Link extraction & filtering
│   ├── nlp/
│   │   ├── preprocessing.py             # spaCy NLP pipeline
│   │   └── embeddings.py                # Sentence-BERT scoring
│   ├── detection/
│   │   └── dark_pattern_detector.py     # Rule + ML hybrid detector
│   ├── vision/
│   │   └── screenshot_analyzer.py       # OpenCV visual analysis
│   ├── graph/
│   │   └── web_graph.py                 # NetworkX graph builder
│   ├── tasks/
│   │   └── celery_tasks.py              # Celery task definitions
│   ├── database/
│   │   └── models.py                    # SQLite models & queries
│   └── screenshots/                     # Captured screenshots
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchPanel.jsx          # Audit input form
│   │   │   ├── ResultsTable.jsx         # Crawled pages table
│   │   │   ├── PatternAlerts.jsx        # Dark pattern alerts
│   │   │   ├── GraphView.jsx            # React Flow graph
│   │   │   └── ScreenshotViewer.jsx     # Screenshot gallery
│   │   ├── pages/
│   │   │   └── Dashboard.jsx            # Main layout
│   │   ├── services/
│   │   │   └── api.js                   # Axios API client
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
│
├── requirements.txt
└── README.md
```

---

## Configuration

### Environment Variables (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URL |
| `MAX_CRAWL_PAGES` | `100` | Hard limit on pages per audit |
| `SCREENSHOT_DIR` | `backend/screenshots/` | Screenshot storage path |

### Relevance Threshold

The **threshold** slider (0.0–1.0) controls how focused the crawl is:
- **0.0** — Crawl all discovered pages regardless of topic relevance
- **0.3** — Default — only follow links from pages with 30%+ relevance
- **0.7** — Highly focused — only follow very relevant pages

---

## Extending the System

### Add a new dark pattern rule

Edit `backend/detection/dark_pattern_detector.py` and add to `DARK_PATTERN_RULES`:

```python
"roach_motel": {
    "description": "Easy to subscribe, hard to cancel.",
    "patterns": [r"(cancel|unsubscribe).*(call|phone|contact|mail)"],
    "keywords": ["call to cancel", "contact us to unsubscribe"],
}
```

### Add a new visual detector

Add a method to `ScreenshotAnalyzer` in `backend/vision/screenshot_analyzer.py`:

```python
def _detect_my_pattern(self, image):
    # OpenCV analysis logic
    return [{"type": "my_pattern", "description": "...", "confidence": 0.8}]
```

Then call it from the `analyze()` method.

---

## License

MIT
