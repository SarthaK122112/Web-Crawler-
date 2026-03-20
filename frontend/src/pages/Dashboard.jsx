import React, { useState, useEffect, useRef, useCallback } from 'react';
import SearchPanel from '../components/SearchPanel';
import ResultsTable from '../components/ResultsTable';
import PatternAlerts from '../components/PatternAlerts';
import GraphView from '../components/GraphView';
import ScreenshotViewer from '../components/ScreenshotViewer';
import { startAudit, getAuditStatus, getResults, getGraphData } from '../services/api';

/**
 * Dashboard — Main application page.
 *
 * Manages audit lifecycle: start → poll → display results.
 * Coordinates all child components and data flow.
 */
const Dashboard = () => {
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('patterns');
  const pollRef = useRef(null);

  // Poll audit status while running
  const pollStatus = useCallback(async (tid) => {
    try {
      const statusData = await getAuditStatus(tid);
      setStatus(statusData);

      if (statusData.status === 'completed' || statusData.status === 'failed') {
        clearInterval(pollRef.current);
        pollRef.current = null;

        if (statusData.status === 'completed') {
          const [resultData, graph] = await Promise.all([
            getResults(tid),
            getGraphData(tid),
          ]);
          setResults(resultData);
          setGraphData(graph);
        }

        if (statusData.status === 'failed') {
          setError('Audit failed. Check server logs for details.');
        }
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }, []);

  const handleStartAudit = async (params) => {
    setError(null);
    setResults(null);
    setGraphData(null);
    setStatus(null);

    try {
      const response = await startAudit(params);
      setTaskId(response.task_id);
      setStatus({ status: 'starting', pages_crawled: 0, pages_total: 0, patterns_found: 0 });

      // Start polling every 2 seconds
      pollRef.current = setInterval(() => pollStatus(response.task_id), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start audit. Is the backend running?');
    }
  };

  const handleStop = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setStatus((prev) => (prev ? { ...prev, status: 'stopped' } : null));
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const isRunning = status?.status === 'running' || status?.status === 'starting';

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-brand">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
          <div>
            <h1>Dark Pattern Detector</h1>
            <p className="header-subtitle">AI-Powered Deceptive Design Analysis</p>
          </div>
        </div>

        {/* Status indicator */}
        {status && (
          <div className={`status-bar ${status.status}`}>
            <div className="status-indicator">
              <span className={`pulse ${isRunning ? 'active' : ''}`} />
              <span className="status-text">
                {status.status === 'completed' ? 'Audit Complete' :
                 status.status === 'failed' ? 'Audit Failed' :
                 status.status === 'stopped' ? 'Stopped' :
                 'Crawling...'}
              </span>
            </div>
            <div className="status-metrics">
              <div className="metric">
                <span className="metric-value">{status.pages_crawled}</span>
                <span className="metric-label">Pages</span>
              </div>
              <div className="metric">
                <span className="metric-value">{status.patterns_found}</span>
                <span className="metric-label">Patterns</span>
              </div>
            </div>
            {isRunning && (
              <div className="progress-track">
                <div className="progress-bar" style={{ width: '100%' }} />
              </div>
            )}
          </div>
        )}
      </header>

      {/* Error display */}
      {error && (
        <div className="error-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Main layout */}
      <div className="dashboard-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <SearchPanel
            onStartAudit={handleStartAudit}
            isRunning={isRunning}
            onStop={handleStop}
          />
        </aside>

        {/* Content area */}
        <main className="content">
          {/* Tabs */}
          <div className="tab-bar">
            {['patterns', 'pages', 'graph', 'screenshots'].map((tab) => (
              <button
                key={tab}
                className={`tab ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'patterns' && '⚠ '}
                {tab === 'pages' && '📄 '}
                {tab === 'graph' && '🔗 '}
                {tab === 'screenshots' && '📸 '}
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                {tab === 'patterns' && results?.patterns?.length > 0 && (
                  <span className="tab-badge">{results.patterns.length}</span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="tab-content">
            {activeTab === 'patterns' && (
              <PatternAlerts patterns={results?.patterns || []} />
            )}
            {activeTab === 'pages' && (
              <ResultsTable
                pages={results?.pages || []}
                patterns={results?.patterns || []}
              />
            )}
            {activeTab === 'graph' && (
              <GraphView graphData={graphData} />
            )}
            {activeTab === 'screenshots' && (
              <ScreenshotViewer screenshots={results?.screenshots || []} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
