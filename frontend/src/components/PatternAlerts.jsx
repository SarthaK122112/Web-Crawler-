import React, { useState } from 'react';

/**
 * PatternAlerts — Displays detected dark patterns with severity indicators.
 *
 * Groups patterns by type and shows confidence scores,
 * evidence snippets, and detection method.
 */

const PATTERN_ICONS = {
  confirmshaming: '😞',
  urgency: '⏰',
  scarcity: '📦',
  misdirection: '🎯',
  social_proof: '👥',
  hidden_costs: '💸',
  trick_question: '❓',
  forced_continuity: '🔄',
  nagging: '🔔',
};

const PATTERN_COLORS = {
  confirmshaming: '#f59e0b',
  urgency: '#ef4444',
  scarcity: '#f97316',
  misdirection: '#8b5cf6',
  social_proof: '#06b6d4',
  hidden_costs: '#ec4899',
  trick_question: '#6366f1',
  forced_continuity: '#14b8a6',
  nagging: '#a855f7',
};

const PatternAlerts = ({ patterns }) => {
  const [expandedId, setExpandedId] = useState(null);
  const [filterType, setFilterType] = useState('all');

  if (!patterns || patterns.length === 0) {
    return (
      <div className="pattern-alerts empty-state">
        <div className="empty-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4">
            <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        </div>
        <p>No dark patterns detected yet.</p>
      </div>
    );
  }

  // Group by type for summary
  const grouped = {};
  patterns.forEach((p) => {
    if (!grouped[p.pattern_type]) grouped[p.pattern_type] = [];
    grouped[p.pattern_type].push(p);
  });

  const types = Object.keys(grouped);
  const filtered = filterType === 'all' ? patterns : patterns.filter((p) => p.pattern_type === filterType);

  return (
    <div className="pattern-alerts">
      <div className="panel-header">
        <div className="panel-icon danger">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <h2>Dark Patterns Detected</h2>
        <span className="badge badge-danger">{patterns.length}</span>
      </div>

      {/* Type summary chips */}
      <div className="pattern-chips">
        <button
          className={`chip ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => setFilterType('all')}
        >
          All ({patterns.length})
        </button>
        {types.map((type) => (
          <button
            key={type}
            className={`chip ${filterType === type ? 'active' : ''}`}
            onClick={() => setFilterType(type)}
            style={{ '--chip-color': PATTERN_COLORS[type] || '#6b7280' }}
          >
            {PATTERN_ICONS[type] || '⚠'} {type.replace(/_/g, ' ')} ({grouped[type].length})
          </button>
        ))}
      </div>

      {/* Pattern cards */}
      <div className="pattern-list">
        {filtered.map((pattern, idx) => {
          const isExpanded = expandedId === idx;
          const color = PATTERN_COLORS[pattern.pattern_type] || '#6b7280';

          return (
            <div
              key={idx}
              className={`pattern-card ${isExpanded ? 'expanded' : ''}`}
              style={{ '--card-accent': color }}
              onClick={() => setExpandedId(isExpanded ? null : idx)}
            >
              <div className="pattern-card-header">
                <span className="pattern-icon">{PATTERN_ICONS[pattern.pattern_type] || '⚠'}</span>
                <div className="pattern-info">
                  <span className="pattern-type">{pattern.pattern_type.replace(/_/g, ' ')}</span>
                  <span className="pattern-url">
                    {(pattern.page_url || '').length > 50
                      ? pattern.page_url.slice(0, 50) + '…'
                      : pattern.page_url}
                  </span>
                </div>
                <div className="pattern-confidence">
                  <div className="confidence-ring" style={{
                    background: `conic-gradient(${color} ${pattern.confidence * 360}deg, var(--color-surface-2) 0deg)`
                  }}>
                    <span>{Math.round(pattern.confidence * 100)}%</span>
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="pattern-card-body">
                  <p className="pattern-description">{pattern.description}</p>
                  {pattern.evidence && (
                    <div className="pattern-evidence">
                      <span className="evidence-label">Evidence:</span>
                      <code>{pattern.evidence}</code>
                    </div>
                  )}
                  <div className="pattern-meta">
                    <span className="method-tag">{pattern.method}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PatternAlerts;
