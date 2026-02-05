🎯 Focused Dark Pattern Web Crawler

An NLP-powered asynchronous web crawler that explores only topic-relevant web pages, detects potential dark patterns, and extracts meaningful content. Built with Python, Streamlit, and spaCy for efficient and ethical web analysis.

✨ Features

🎯 Topic-focused crawling using semantic similarity (spaCy)

🕷️ Asynchronous crawling with Aiohttp + Asyncio

🚨 Detects potential dark patterns (keywords & CSS classes)

🤖 Respects robots.txt

📊 Real-time progress tracking

📁 CSV export for results

🖥️ Interactive UI using Streamlit

🛠 Tech Stack

Python

Streamlit

Aiohttp & Asyncio

BeautifulSoup

spaCy (en_core_web_md)

Pandas

Regex

⚙️ How It Works

Enter a start URL and target topic

The crawler:

Computes semantic similarity using spaCy

Visits only relevant pages

From relevant pages, it:

Extracts <h1> titles

Detects dark patterns (urgency, confirm shaming, hidden costs, etc.)

Relevant links are queued recursively

Results are displayed live and downloadable as CSV

🚨 Dark Pattern Detection

The crawler flags potential dark patterns using:

Keyword matching
(e.g. limited time offer, only 2 left in stock)

Suspicious CSS classes
(e.g. confirm-shame, hidden-cost, high-demand)

Each finding includes:

URL

Pattern type

Matched content

Context (when available)

📦 Installation
git clone https://github.com/your-username/focused-dark-pattern-crawler.git
cd focused-dark-pattern-crawler
pip install -r requirements.txt
python -m spacy download en_core_web_md

▶️ Run the App
streamlit run app.py

📤 Output

📄 H1 Titles CSV

🚨 Dark Pattern Findings CSV

📊 Live tables in Streamlit UI

📌 Use Cases

Dark pattern research

Ethical UX analysis

NLP-based web scraping

Academic & learning projects

⚠️ Disclaimer

This tool identifies potential dark patterns using heuristics and NLP similarity. Results should be reviewed manually and are not legal conclusions.

👨‍💻 Author

Sarthak Khare
