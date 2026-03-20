import React, { useState } from 'react';

/**
 * SearchPanel — Input form for starting a dark pattern audit.
 *
 * Collects URL, topic, max pages, and relevance threshold,
 * then dispatches the audit via the onStartAudit callback.
 */
const SearchPanel = ({ onStartAudit, isRunning, onStop }) => {
  const [url, setUrl] = useState('');
  const [topic, setTopic] = useState('');
  const [maxPages, setMaxPages] = useState(20);
  const [threshold, setThreshold] = useState(0.3);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    onStartAudit({
      url: url.trim(),
      topic: topic.trim() || 'dark patterns',
      max_pages: maxPages,
      threshold: threshold,
    });
  };

  return (
    <div className="search-panel">
      <div className="panel-header">
        <div className="panel-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </div>
        <h2>Audit Configuration</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="url">Target URL</label>
          <input
            id="url"
            type="url"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            disabled={isRunning}
          />
        </div>

        <div className="form-group">
          <label htmlFor="topic">Topic / Keyword</label>
          <input
            id="topic"
            type="text"
            placeholder="e.g. dark patterns, pricing, subscription"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={isRunning}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="maxPages">Max Pages</label>
            <input
              id="maxPages"
              type="number"
              min={1}
              max={100}
              value={maxPages}
              onChange={(e) => setMaxPages(parseInt(e.target.value) || 1)}
              disabled={isRunning}
            />
          </div>
          <div className="form-group">
            <label htmlFor="threshold">
              Relevance Threshold
              <span className="threshold-value">{threshold.toFixed(2)}</span>
            </label>
            <input
              id="threshold"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              disabled={isRunning}
            />
          </div>
        </div>

        <div className="button-row">
          {!isRunning ? (
            <button type="submit" className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Audit
            </button>
          ) : (
            <button type="button" className="btn btn-danger" onClick={onStop}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              Stop Audit
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default SearchPanel;
