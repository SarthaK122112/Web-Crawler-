import React, { useState } from 'react';

/**
 * ScreenshotViewer — Displays captured webpage screenshots.
 *
 * Shows a thumbnail grid with click-to-expand modal view.
 * Each screenshot shows the analysis result summary.
 */
const ScreenshotViewer = ({ screenshots }) => {
  const [selectedIdx, setSelectedIdx] = useState(null);

  if (!screenshots || screenshots.length === 0) {
    return (
      <div className="screenshot-viewer empty-state">
        <div className="empty-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
        </div>
        <p>No screenshots captured yet.</p>
      </div>
    );
  }

  const getImageUrl = (filepath) => {
    // Extract filename from full path
    const parts = filepath.split('/');
    const filename = parts[parts.length - 1];
    return `http://localhost:8000/screenshots/${filename}`;
  };

  const selected = selectedIdx !== null ? screenshots[selectedIdx] : null;

  return (
    <div className="screenshot-viewer">
      <div className="panel-header">
        <div className="panel-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
        </div>
        <h2>Screenshots</h2>
        <span className="badge">{screenshots.length}</span>
      </div>

      <div className="screenshot-grid">
        {screenshots.map((ss, idx) => (
          <div
            key={idx}
            className="screenshot-card"
            onClick={() => setSelectedIdx(idx)}
          >
            <div className="screenshot-thumb">
              <img
                src={getImageUrl(ss.filepath)}
                alt={`Screenshot of ${ss.page_url}`}
                loading="lazy"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.classList.add('img-error');
                }}
              />
            </div>
            <div className="screenshot-info">
              <span className="screenshot-url">
                {ss.page_url.length > 40 ? ss.page_url.slice(0, 40) + '…' : ss.page_url}
              </span>
              {ss.analysis_result && ss.analysis_result !== 'No visual issues detected' && (
                <span className="screenshot-alert">⚠ {ss.analysis_result}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox modal */}
      {selected && (
        <div className="screenshot-modal" onClick={() => setSelectedIdx(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedIdx(null)}>✕</button>
            <img
              src={getImageUrl(selected.filepath)}
              alt={`Screenshot of ${selected.page_url}`}
            />
            <div className="modal-info">
              <a href={selected.page_url} target="_blank" rel="noopener noreferrer">
                {selected.page_url}
              </a>
              {selected.analysis_result && (
                <p className="modal-analysis">{selected.analysis_result}</p>
              )}
            </div>

            <div className="modal-nav">
              <button
                disabled={selectedIdx === 0}
                onClick={() => setSelectedIdx(selectedIdx - 1)}
              >
                ← Previous
              </button>
              <span>{selectedIdx + 1} / {screenshots.length}</span>
              <button
                disabled={selectedIdx === screenshots.length - 1}
                onClick={() => setSelectedIdx(selectedIdx + 1)}
              >
                Next →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScreenshotViewer;
