"""
Web graph construction and visualization.

Builds a directed graph of crawled pages and their hyperlink relationships
using NetworkX. Exports data for frontend visualization and can generate
standalone HTML visualizations with PyVis.
"""

import os
import logging
from typing import Dict, List, Optional

import networkx as nx

logger = logging.getLogger(__name__)

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False


class WebGraphBuilder:
    """
    Builds and manages a directed graph of web pages.

    Nodes represent crawled pages; edges represent hyperlinks.
    Supports marking nodes with dark-pattern detection status
    and exporting to multiple visualization formats.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, url: str, title: str = "", relevance: float = 0.0, has_pattern: bool = False):
        """
        Add a page node to the graph.

        Args:
            url: Page URL (used as the node identifier).
            title: Page title for display.
            relevance: Semantic relevance score (0–1).
            has_pattern: Whether dark patterns were detected on this page.
        """
        self.graph.add_node(
            url,
            title=title or url,
            relevance=relevance,
            has_pattern=has_pattern,
            color="#ef4444" if has_pattern else "#3b82f6",
        )

    def add_edge(self, source: str, target: str):
        """Add a directed hyperlink edge between two pages."""
        self.graph.add_edge(source, target)

    def get_stats(self) -> Dict:
        """Return summary statistics about the graph."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
            "is_connected": nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
        }

    def get_central_nodes(self, top_n: int = 5) -> List[Dict]:
        """
        Return the most central nodes by PageRank.

        Useful for identifying the most interconnected or "hub" pages.
        """
        if self.graph.number_of_nodes() == 0:
            return []

        pagerank = nx.pagerank(self.graph)
        sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "url": url,
                "pagerank": round(score, 4),
                "title": self.graph.nodes[url].get("title", url),
                "has_pattern": self.graph.nodes[url].get("has_pattern", False),
            }
            for url, score in sorted_nodes[:top_n]
        ]

    def to_react_flow(self) -> Dict:
        """
        Export graph data in React Flow-compatible format.

        Returns:
            Dict with 'nodes' and 'edges' arrays ready for React Flow.
        """
        nodes = []
        for i, (url, data) in enumerate(self.graph.nodes(data=True)):
            nodes.append({
                "id": url,
                "data": {
                    "label": (data.get("title", url))[:40],
                    "relevance": data.get("relevance", 0),
                    "has_pattern": data.get("has_pattern", False),
                },
                "position": {"x": (i % 6) * 220, "y": (i // 6) * 140},
                "style": {
                    "background": data.get("color", "#3b82f6"),
                    "color": "#ffffff",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "fontSize": "11px",
                    "border": "2px solid rgba(255,255,255,0.2)",
                },
            })

        edges = [
            {
                "id": f"e-{s[:16]}-{t[:16]}",
                "source": s,
                "target": t,
                "animated": True,
                "style": {"stroke": "#94a3b8"},
            }
            for s, t in self.graph.edges()
        ]

        return {"nodes": nodes, "edges": edges}

    def export_pyvis_html(self, output_path: str = "graph.html") -> Optional[str]:
        """
        Generate a standalone interactive HTML visualization using PyVis.

        Args:
            output_path: Where to save the HTML file.

        Returns:
            Path to the generated file, or None if PyVis is unavailable.
        """
        if not PYVIS_AVAILABLE:
            logger.warning("PyVis not installed — cannot export HTML graph")
            return None

        net = Network(height="700px", width="100%", directed=True, bgcolor="#0f172a")
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)

        for url, data in self.graph.nodes(data=True):
            color = "#ef4444" if data.get("has_pattern") else "#3b82f6"
            size = 20 + (data.get("relevance", 0) * 20)
            net.add_node(
                url,
                label=(data.get("title", url))[:30],
                color=color,
                size=size,
                title=f"{data.get('title', url)}\nRelevance: {data.get('relevance', 0):.2f}",
            )

        for source, target in self.graph.edges():
            net.add_edge(source, target, color="#475569")

        net.save_graph(output_path)
        return output_path
