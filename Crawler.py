import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import csv
import urllib.robotparser
from urllib.parse import urljoin, urlparse
import pandas as pd
from io import StringIO

# --- Web Crawler Class ---
class WebCrawler:
    def __init__(self, start_url, max_pages=100):
        self.start_url = start_url
        self.max_pages = max_pages
        self.visited = set()
        self.to_visit = set([start_url])
        self.data = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return (
            url not in self.visited
            and parsed.scheme in ["http", "https"]
            and not parsed.fragment
            and not parsed.path.startswith("javascript")
        )

    def respect_robots_txt(self, url):
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            return True  # Fail open

    def crawl(self, progress_callback=None):
        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.pop()

            # if not self.is_valid_url(url) or not self.respect_robots_txt(url):
            #     continue

            try:
                response = requests.get(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    self.visited.add(url)
                    self.parse_page(response.text, url)
            except requests.RequestException:
                continue

            if progress_callback:
                progress_callback(len(self.visited) / self.max_pages)
            time.sleep(1)

    def parse_page(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")

        # Collect all H1 tags
        for title in soup.find_all("h1"):
            text = title.get_text(strip=True)
            if text:
                self.data.append({"URL": base_url, "Title": text})

        # Add new links to the to_visit set
        for link in soup.find_all("a", href=True):
            full_url = urljoin(base_url, link["href"])
            if self.is_valid_url(full_url):
                self.to_visit.add(full_url)

    def get_data_as_csv(self):
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["URL", "Title"])
        writer.writeheader()
        for item in self.data:
            writer.writerow(item)
        return output.getvalue()

# --- Streamlit App Interface ---
st.set_page_config(page_title="Web Crawler", layout="wide")
st.title("🕷️ Web Crawler using Streamlit")
st.markdown("Enter a starting URL to crawl the web and extract `<h1>` titles from pages.")

# Sidebar Inputs
with st.sidebar:
    st.header("Crawler Settings")
    start_url = st.text_input("🔗 Start URL", "https://example.com")
    max_pages = st.slider("📄 Max Pages", 5, 200, 20)
    crawl_button = st.button("🚀 Start Crawling")

if crawl_button:
    if not start_url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("Crawling... Please wait."):
            crawler = WebCrawler(start_url, max_pages)
            progress = st.progress(0.0)
            crawler.crawl(progress_callback=progress.progress)
            csv_data = crawler.get_data_as_csv()

        st.success(f"✅ Completed! {len(crawler.visited)} pages visited, {len(crawler.data)} titles extracted.")
        df = pd.read_csv(StringIO(csv_data))

        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Download CSV", csv_data, "web_crawler_data.csv", "text/csv")
        else:
            st.warning("No titles found in the crawled pages.")
