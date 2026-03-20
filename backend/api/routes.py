"""
FastAPI REST API routes.

Provides endpoints for starting audits, checking status,
retrieving results, and fetching graph/screenshot data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import uuid

from backend.database.models import (
    get_audit, get_crawled_pages, get_patterns,
    get_screenshots, get_edges,
)
from backend.tasks.celery_tasks import run_audit_task

router = APIRouter()


# ── Request / Response Models ───────────────────────────────

class AuditRequest(BaseModel):
    """Schema for starting a new audit."""
    url: str
    topic: str
    max_pages: int = 20
    threshold: float = 0.3


class AuditResponse(BaseModel):
    """Schema returned when an audit is created."""
    task_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    """Schema for audit status polling."""
    task_id: str
    status: str
    pages_crawled: int
    pages_total: int
    patterns_found: int


# ── Endpoints ───────────────────────────────────────────────

@router.post("/start-audit", response_model=AuditResponse)
async def start_audit(request: AuditRequest):
    """
    Start a new dark-pattern audit.

    Dispatches a Celery background task that handles crawling,
    NLP analysis, and pattern detection asynchronously.
    """
    task_id = str(uuid.uuid4())

    # Dispatch to Celery
    run_audit_task.delay(
        task_id=task_id,
        url=request.url,
        topic=request.topic,
        max_pages=request.max_pages,
        threshold=request.threshold,
    )

    return AuditResponse(
        task_id=task_id,
        status="started",
        message="Audit task queued successfully.",
    )


@router.get("/audit-status/{task_id}", response_model=StatusResponse)
async def audit_status(task_id: str):
    """
    Poll the current status of an audit task.

    Returns progress metrics including pages crawled and patterns found.
    """
    audit = get_audit(task_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    return StatusResponse(
        task_id=task_id,
        status=audit["status"],
        pages_crawled=audit["pages_crawled"],
        pages_total=audit["pages_total"],
        patterns_found=audit["patterns_found"],
    )


@router.get("/results/{task_id}")
async def get_results(task_id: str):
    """
    Retrieve the full results of a completed audit.

    Returns crawled pages, detected dark patterns, screenshot metadata,
    and graph edge data.
    """
    audit = get_audit(task_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    pages = get_crawled_pages(task_id)
    patterns = get_patterns(task_id)
    screenshots = get_screenshots(task_id)
    edges = get_edges(task_id)

    return {
        "audit": audit,
        "pages": pages,
        "patterns": patterns,
        "screenshots": screenshots,
        "graph": {
            "nodes": [
                {
                    "id": p["url"],
                    "label": p["title"] or p["url"],
                    "relevance": p["relevance_score"],
                    "has_pattern": any(pat["page_url"] == p["url"] for pat in patterns),
                }
                for p in pages
            ],
            "edges": [
                {"source": e["source_url"], "target": e["target_url"]}
                for e in edges
            ],
        },
    }


@router.get("/patterns/{task_id}")
async def get_task_patterns(task_id: str):
    """Retrieve all detected dark patterns for a specific audit."""
    patterns = get_patterns(task_id)
    return {"task_id": task_id, "patterns": patterns, "count": len(patterns)}


@router.get("/screenshots/{task_id}")
async def get_task_screenshots(task_id: str):
    """Retrieve all screenshot records for a specific audit."""
    screenshots = get_screenshots(task_id)
    return {"task_id": task_id, "screenshots": screenshots}


@router.get("/graph/{task_id}")
async def get_graph_data(task_id: str):
    """
    Retrieve graph data for visualization.

    Returns nodes (pages) and edges (hyperlinks) in a format
    compatible with React Flow.
    """
    pages = get_crawled_pages(task_id)
    edges = get_edges(task_id)
    patterns = get_patterns(task_id)

    pattern_urls = {p["page_url"] for p in patterns}

    nodes = []
    for i, page in enumerate(pages):
        nodes.append({
            "id": page["url"],
            "data": {
                "label": (page["title"] or page["url"])[:40],
                "relevance": page["relevance_score"],
                "has_pattern": page["url"] in pattern_urls,
            },
            "position": {"x": (i % 5) * 250, "y": (i // 5) * 150},
            "style": {
                "background": "#ef4444" if page["url"] in pattern_urls else "#3b82f6",
                "color": "#fff",
                "borderRadius": "8px",
                "padding": "10px",
                "fontSize": "11px",
            },
        })

    flow_edges = [
        {
            "id": f"e-{e['source_url'][:20]}-{e['target_url'][:20]}",
            "source": e["source_url"],
            "target": e["target_url"],
            "animated": True,
        }
        for e in edges
    ]

    return {"nodes": nodes, "edges": flow_edges}
