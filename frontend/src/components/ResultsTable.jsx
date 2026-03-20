import React, { useState } from 'react';

/**
 * ResultsTable — Displays crawled pages with relevance scores.
 *
 * Sortable by relevance or title. Highlights pages where
 * dark patterns were detected.
 */
const ResultsTable = ({ pages, patterns }) => {
  const [sortField, setSortField] = useState('relevance_score');
  const [sortDir, setSortDir] = useState('desc');

  if (!pages || pages.length === 0) {
    return (
      <div className="results-table empty-state">
        <div className="empty-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        </div>
        <p>No pages crawled yet. Start an audit to see results.</p>
      </div>
    );
  }

  const patternUrls = new Set((patterns || []).map((p) => p.page_url));

  const sorted = [...pages].sort((a, b) => {
    const aVal = a[sortField] || '';
    const bVal = b[sortField] || '';
    if (sortDir === 'asc') return aVal > bVal ? 1 : -1;
    return aVal < bVal ? 1 : -1;
  });

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const arrow = (field) => {
    if (sortField !== field) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  return (
    <div className="results-table">
      <div className="panel-header">
        <div className="panel-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18M9 21V9" />
          </svg>
        </div>
        <h2>Crawled Pages</h2>
        <span className="badge">{pages.length}</span>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th className="col-status">#</th>
              <th className="col-url" onClick={() => toggleSort('url')}>
                URL{arrow('url')}
              </th>
              <th className="col-title" onClick={() => toggleSort('title')}>
                Title{arrow('title')}
              </th>
              <th className="col-score" onClick={() => toggleSort('relevance_score')}>
                Relevance{arrow('relevance_score')}
              </th>
              <th className="col-patterns">Patterns</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((page, i) => {
              const hasPattern = patternUrls.has(page.url);
              return (
                <tr key={page.url || i} className={hasPattern ? 'row-flagged' : ''}>
                  <td className="col-status">
                    {hasPattern ? (
                      <span className="status-dot danger" title="Dark patterns detected">⚠</span>
                    ) : (
                      <span className="status-dot safe" title="No patterns detected">✓</span>
                    )}
                  </td>
                  <td className="col-url">
                    <a href={page.url} target="_blank" rel="noopener noreferrer">
                      {page.url.length > 60 ? page.url.slice(0, 60) + '…' : page.url}
                    </a>
                  </td>
                  <td className="col-title">{page.title || '—'}</td>
                  <td className="col-score">
                    <div className="score-bar-container">
                      <div
                        className="score-bar"
                        style={{
                          width: `${(page.relevance_score || 0) * 100}%`,
                          background: page.relevance_score > 0.6
                            ? 'var(--color-success)'
                            : page.relevance_score > 0.3
                            ? 'var(--color-warning)'
                            : 'var(--color-muted)',
                        }}
                      />
                      <span className="score-label">{(page.relevance_score || 0).toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="col-patterns">
                    {hasPattern ? (
                      <span className="tag tag-danger">Detected</span>
                    ) : (
                      <span className="tag tag-safe">Clean</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResultsTable;
