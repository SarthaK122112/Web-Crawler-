🎯 Focused Dark Pattern Web Crawler
An asynchronous, NLP-driven web crawler built with Python and Streamlit that selectively crawls topic-relevant web pages, detects potential dark patterns, and extracts meaningful content. The crawler uses spaCy semantic similarity to focus only on relevant pages, ensuring efficient and targeted crawling.

🚀 Features
🔍 Topic-Focused Crawling using NLP similarity scoring
🧠 spaCy-powered Semantic Filtering (en_core_web_md)
🚨 Dark Pattern Detection via keyword and CSS class analysis
🕷️ Asynchronous Crawling with concurrency control (Aiohttp + Asyncio)
🤖 robots.txt Compliance
📊 Real-time Progress Tracking
📁 CSV Export for extracted titles and dark pattern findings
🖥️ Interactive UI built with Streamlit

🛠️ Tech Stack
Language: Python
Framework: Streamlit
Web Crawling: Aiohttp, Asyncio
HTML Parsing: BeautifulSoup
NLP: spaCy (en_core_web_md)
Data Handling: Pandas, CSV
Others: Regex, urllib

🧩 How It Works
User provides a start URL and target topic.
The crawler converts the topic into a spaCy document.
Each visited page is:
   Checked for semantic relevance using cosine similarity.
   Parsed only if it exceeds a relevance threshold.
Relevant pages are scanned for:
   <h1> titles
   Dark patterns (e.g., urgency phrases, hidden costs).
   Only relevant links are added to the crawl queue.
   Results are displayed live and downloadable as CSV files.

🚨 Dark Pattern Detection
The crawler identifies potential dark patterns using:
Keyword-based patterns
(e.g., “only 2 left in stock”, “limited time offer”)
Suspicious CSS classes
(e.g., confirm-shame, hidden-cost, high-demand)
Each finding includes:
   URL
   Pattern type
   Matched keyword or CSS class
   Context (when available)

📄 Output
H1 Titles CSV – Extracted from topic-relevant pages
Dark Patterns CSV – Potential dark patterns with context
Live Tables displayed in the Streamlit UI

📌 Use Cases
Dark pattern research & analysis
Ethical UX auditing
Web scraping with NLP filtering
Academic and research projects
Responsible web crawling demonstrations
