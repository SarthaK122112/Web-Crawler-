"""
Celery task definitions for background processing.

Configures the Celery application with Redis as the broker and
defines the main audit workflow that orchestrates crawling, NLP,
dark-pattern detection, and graph construction.

Run worker with:
    celery -A backend.tasks.celery_tasks worker --loglevel=info
"""

from celery import Celery
import logging

logger = logging.getLogger(__name__)

# ── Celery Configuration ────────────────────────────────────

celery_app = Celery(
    "dark_pattern_detector",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="run_audit_task", max_retries=2)
def run_audit_task(self, task_id: str, url: str, topic: str, max_pages: int, threshold: float):
    """
    Main audit orchestration task.

    Coordinates the full pipeline:
      1. Create audit record in DB
      2. Initialize the semantic crawler
      3. Crawl pages with priority-based link following
      4. Run NLP preprocessing & relevance scoring
      5. Detect dark patterns (rule-based + ML)
      6. Capture and analyze screenshots
      7. Build link graph
      8. Update final status

    Args:
        task_id: Unique identifier for this audit run.
        url: Starting URL to crawl.
        topic: Keyword/topic for semantic relevance.
        max_pages: Maximum number of pages to crawl.
        threshold: Minimum relevance score to continue crawling.
    """
    from backend.database.models import (
        create_audit, update_audit_status, insert_crawled_page,
        insert_pattern, insert_edge, insert_screenshot,
    )
    from backend.crawler.crawler import SemanticCrawler
    from backend.nlp.preprocessing import NLPPreprocessor
    from backend.nlp.embeddings import SemanticScorer
    from backend.detection.dark_pattern_detector import DarkPatternDetector
    from backend.vision.screenshot_analyzer import ScreenshotAnalyzer
    from backend.graph.web_graph import WebGraphBuilder

    try:
        # Step 1: Register the audit
        create_audit(task_id, url, topic, max_pages, threshold)
        logger.info(f"[{task_id}] Audit started for {url} — topic: '{topic}'")

        # Step 2: Initialize components
        preprocessor = NLPPreprocessor()
        scorer = SemanticScorer()
        detector = DarkPatternDetector()
        vision = ScreenshotAnalyzer(task_id=task_id)
        graph = WebGraphBuilder()
        crawler = SemanticCrawler(max_pages=max_pages)

        # Step 3: Compute topic embedding
        topic_embedding = scorer.encode(topic)

        # Step 4: Crawl
        pages_crawled = 0
        crawler.add_to_queue(url, priority=1.0)

        while crawler.has_next() and pages_crawled < max_pages:
            current_url = crawler.get_next()
            if not current_url:
                break

            logger.info(f"[{task_id}] Crawling ({pages_crawled + 1}/{max_pages}): {current_url}")

            # Fetch page
            page_data = crawler.fetch_page(current_url)
            if not page_data:
                continue

            title = page_data.get("title", "")
            raw_html = page_data.get("html", "")
            text_content = page_data.get("text", "")
            links = page_data.get("links", [])
            screenshot_path = page_data.get("screenshot_path")

            # Step 5: NLP preprocessing
            processed_text = preprocessor.process(text_content)

            # Step 6: Relevance scoring
            if processed_text:
                page_embedding = scorer.encode(processed_text)
                relevance = scorer.similarity(topic_embedding, page_embedding)
            else:
                relevance = 0.0

            # Store crawled page
            insert_crawled_page(task_id, current_url, title, relevance, len(text_content))
            pages_crawled += 1

            # Step 7: Detect dark patterns
            if processed_text:
                patterns = detector.detect(text_content, raw_html)
                for p in patterns:
                    insert_pattern(
                        task_id=task_id,
                        page_url=current_url,
                        pattern_type=p["type"],
                        description=p["description"],
                        confidence=p["confidence"],
                        evidence=p["evidence"],
                        method=p["method"],
                    )

            # Step 8: Screenshot analysis
            if screenshot_path:
                visual_issues = vision.analyze(screenshot_path, current_url)
                analysis_summary = "; ".join(
                    [f"{v['type']} (conf: {v['confidence']:.2f})" for v in visual_issues]
                ) if visual_issues else "No visual issues detected"

                insert_screenshot(task_id, current_url, screenshot_path, analysis_summary)

                for v in visual_issues:
                    insert_pattern(
                        task_id=task_id,
                        page_url=current_url,
                        pattern_type=v["type"],
                        description=v["description"],
                        confidence=v["confidence"],
                        evidence="visual_analysis",
                        method="computer_vision",
                    )

            # Step 9: Build graph edges & enqueue discovered links
            for link in links:
                insert_edge(task_id, current_url, link)
                graph.add_edge(current_url, link)

                if relevance >= threshold:
                    crawler.add_to_queue(link, priority=relevance)

            # Update progress
            total_patterns = len(detector.detect(text_content, raw_html)) if processed_text else 0
            update_audit_status(task_id, "running", pages_crawled=pages_crawled)

        # Step 10: Finalize
        crawler.close()
        total_patterns_count = len(
            [p for p in (get_patterns_helper(task_id))]
        ) if pages_crawled > 0 else 0

        update_audit_status(task_id, "completed", pages_crawled=pages_crawled, patterns_found=total_patterns_count)
        logger.info(f"[{task_id}] Audit completed. Pages: {pages_crawled}")
        return {"task_id": task_id, "status": "completed", "pages": pages_crawled}

    except Exception as exc:
        logger.error(f"[{task_id}] Audit failed: {exc}", exc_info=True)
        try:
            update_audit_status(task_id, "failed")
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)


def get_patterns_helper(task_id):
    """Helper to retrieve patterns count for final status update."""
    from backend.database.models import get_patterns
    return get_patterns(task_id)
