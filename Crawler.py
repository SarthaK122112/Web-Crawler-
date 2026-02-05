import streamlit as st
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import csv
import urllib.robotparser
from urllib.parse import urljoin, urlparse
import pandas as pd
from io import StringIO
import re
import spacy  # Import spaCy

# --- Load spaCy Model (Cached) ---
# We cache this so it only loads once on app startup
@st.cache_resource
def load_spacy_model():
    try:
        # Using md model for better vectors
        model = spacy.load("en_core_web_md") 
    except IOError:
        st.error("spaCy model 'en_core_web_md' not found. Please run: \n"
                 "python -m spacy download en_core_web_md")
        return None
    return model

# --- Dark Pattern Definitions ---
DARK_PATTERNS = {
    "keywords": [
        r"only \d+ left in stock", r"limited time offer",
        r"offer expires (today|soon)", r"hurry up", r"high demand",
        r"sneak into basket", r"confirmshaming"
    ],
    "css_classes": [
        "dark-pattern", "confirm-shame", "low-stock", "high-demand",
        "hidden-cost", "visually-hidden"
    ]
}

# --- Web Crawler Class (Async + Focused) ---
class WebCrawler:
    def __init__(self, start_url, max_pages, concurrency, nlp, target_topic):
        self.start_url = start_url
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.visited = set()
        self.data = []  # For H1 titles
        self.dark_pattern_findings = []  # For dark patterns
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        self.queue = asyncio.Queue()
        self.in_queue = set()

        # --- NLP & Focus ---
        self.nlp = nlp
        self.target_doc = nlp(target_topic) # Process target topic once
        self.relevancy_threshold = 0.3 # Hardcoded threshold (0.0 to 1.0)
        # ---

    def is_valid_url_structure(self, url):
        parsed = urlparse(url)
        return (
            parsed.scheme in ["http", "https"] and not parsed.fragment and
            not parsed.path.startswith("javascript")
        )

    # ... (respect_robots_txt, fetch, and worker methods are unchanged) ...
    def respect_robots_txt(self, url):
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            return True

    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        return None

    async def worker(self, session, progress_callback):
        while True:
            try:
                url = await self.queue.get()
                if len(self.visited) >= self.max_pages:
                    self.queue.task_done()
                    continue

                html = await self.fetch(session, url)
                self.visited.add(url)
                if html:
                    # NLP processing happens here (synchronously)
                    self.parse_page(html, url) 
                
                if progress_callback:
                    progress_callback(min(1.0, len(self.visited) / self.max_pages))
                self.queue.task_done()
            except asyncio.CancelledError:
                return
            except Exception:
                self.queue.task_done()
                continue
    # ...

    async def crawl(self, progress_callback=None):
        self.queue = asyncio.Queue()
        self.in_queue = set([self.start_url])
        self.queue.put_nowait(self.start_url)
        
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(headers=self.headers, connector=connector) as session:
            workers = [
                asyncio.create_task(self.worker(session, progress_callback))
                for _ in range(self.concurrency)
            ]
            await self.queue.join()
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    def parse_page(self, html, base_url):
        """
        Parses HTML, checks relevancy, extracts data, 
        and adds relevant links to the queue.
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # --- 1. Page Relevancy Check ---
        page_text = soup.get_text(strip=True)
        if not page_text:
            return  # Skip empty pages
        
        page_doc = self.nlp(page_text)
        page_similarity = page_doc.similarity(self.target_doc)

        # --- 2. Data Extraction (Only if page is relevant) ---
        if page_similarity > self.relevancy_threshold:
            # Collect H1 Tags
            for title in soup.find_all("h1"):
                text = title.get_text(strip=True)
                if text:
                    self.data.append({"URL": base_url, "Title": text})
            
            # Find Dark Patterns
            page_text_lower = page_text.lower()
            for keyword_pattern in DARK_PATTERNS["keywords"]:
                matches = re.findall(keyword_pattern, page_text_lower)
                for match in matches:
                    self.dark_pattern_findings.append({
                        "URL": base_url, "Pattern_Type": "Keyword", "Finding": match
                    })
            for css_class in DARK_PATTERNS["css_classes"]:
                elements = soup.find_all(class_=css_class)
                for el in elements:
                    self.dark_pattern_findings.append({
                        "URL": base_url, "Pattern_Type": "CSS Class",
                        "Finding": css_class,
                        "Context": el.get_text(strip=True)[:100] + "..."
                    })

        # --- 3. Link Relevancy Check (Follow relevant links) ---
        for link in soup.find_all("a", href=True):
            anchor_text = link.get_text(strip=True)
            full_url = urljoin(base_url, link["href"])
            
            # Basic checks first (fast)
            if (not anchor_text or
                full_url in self.visited or
                full_url in self.in_queue or
                not self.is_valid_url_structure(full_url)):
                continue
                
            # NLP check (slower)
            link_doc = self.nlp(anchor_text)
            link_similarity = link_doc.similarity(self.target_doc)
            
            if link_similarity > self.relevancy_threshold:
                self.in_queue.add(full_url)
                self.queue.put_nowait(full_url)

    # ... (get_data_as_csv and get_dark_patterns_as_csv are unchanged) ...
    def get_data_as_csv(self):
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["URL", "Title"])
        writer.writeheader()
        for item in self.data:
            writer.writerow(item)
        return output.getvalue()

    def get_dark_patterns_as_csv(self):
        if not self.dark_pattern_findings:
            return ""
        output = StringIO()
        fieldnames = ["URL", "Pattern_Type", "Finding", "Context"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for item in self.dark_pattern_findings:
             row = {k: item.get(k, "") for k in fieldnames}
             writer.writerow(row)
        return output.getvalue()
    # ...

# --- Streamlit App Interface ---
st.set_page_config(page_title="Focused Crawler", layout="wide")
st.title("🎯 Focused Dark Pattern Crawler")
st.markdown("Enter a URL and a topic. The crawler will only explore relevant pages.")

# Load the NLP model
nlp_model = load_spacy_model()

# Sidebar Inputs
with st.sidebar:
    st.header("Crawler Settings")
    start_url = st.text_input("🔗 Start URL", "https.en.wikipedia.org/wiki/Web_scraping")
    target_topic = st.text_input("🎯 Target Topic", "data mining")
    crawl_button = st.button("🚀 Start Crawling")

if nlp_model is None:
    st.stop() # Stop if model didn't load

if crawl_button:
    if not start_url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
    elif not target_topic:
        st.error("Please enter a target topic.")
    else:
        with st.spinner(f"Crawling for '{target_topic}'... Please wait. (NLP processing takes time)"):
            crawler = WebCrawler(
                start_url,
                max_pages=50,
                concurrency=10,
                nlp=nlp_model,
                target_topic=target_topic
            )
            progress = st.progress(0.0)
            
            asyncio.run(crawler.crawl(progress_callback=progress.progress))
            
            title_csv_data = crawler.get_data_as_csv()
            dark_pattern_csv_data = crawler.get_dark_patterns_as_csv()

        st.success(f"✅ Completed! {len(crawler.visited)} pages visited.")
        
        # --- Display Dark Pattern Results ---
        st.subheader("🚨 Dark Pattern Findings")
        if dark_pattern_csv_data:
            df_dark = pd.read_csv(StringIO(dark_pattern_csv_data))
            st.warning(f"Found {len(df_dark)} potential dark patterns on relevant pages.")
            st.dataframe(df_dark, use_container_width=True)
            st.download_button("📥 Download Dark Pattern CSV", dark_pattern_csv_data, "dark_patterns.csv", "text/csv")
        else:
            st.info("No dark patterns found on relevant pages.")
        
        st.divider()

        # --- Display Title Results ---
        st.subheader(f"📄 Extracted H1 Titles (Topic: '{target_topic}')")
        if title_csv_data:
            try:
                df_titles = pd.read_csv(StringIO(title_csv_data))
                if not df_titles.empty:
                    st.dataframe(df_titles, use_container_width=True)
                    st.download_button("📥 Download Titles CSV", title_csv_data, "web_crawler_data.csv", "text/csv")
                else:
                    st.warning("No H1 titles found on relevant pages.")
            except pd.errors.EmptyDataError:
                 st.warning("No H1 titles found on relevant pages.")
        else:
            st.warning("No H1 titles found on relevant pages.")
