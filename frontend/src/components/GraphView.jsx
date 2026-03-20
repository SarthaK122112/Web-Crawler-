import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

/**
 * GraphView — Interactive web graph visualization using React Flow.
 *
 * Displays crawled pages as nodes and hyperlinks as edges.
 * Nodes containing dark patterns are highlighted in red.
 */
const GraphView = ({ graphData }) => {
  const initialNodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    return graphData.nodes.map((node, i) => ({
      ...node,
      position: node.position || { x: (i % 5) * 250, y: Math.floor(i / 5) * 150 },
      type: 'default',
      style: {
        background: node.data?.has_pattern ? '#dc2626' : '#2563eb',
        color: '#fff',
        borderRadius: '10px',
        padding: '10px 14px',
        fontSize: '11px',
        fontFamily: "'JetBrains Mono', monospace",
        border: node.data?.has_pattern
          ? '2px solid #fca5a5'
          : '2px solid rgba(255,255,255,0.15)',
        boxShadow: node.data?.has_pattern
          ? '0 0 20px rgba(220,38,38,0.3)'
          : '0 4px 12px rgba(0,0,0,0.2)',
      },
    }));
  }, [graphData]);

  const initialEdges = useMemo(() => {
    if (!graphData?.edges) return [];
    return graphData.edges.map((edge) => ({
      ...edge,
      animated: true,
      style: { stroke: '#475569', strokeWidth: 1.5 },
    }));
  }, [graphData]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  if (!graphData || (!graphData.nodes?.length && !graphData.edges?.length)) {
    return (
      <div className="graph-view empty-state">
        <div className="empty-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4">
            <circle cx="12" cy="12" r="2" />
            <circle cx="6" cy="6" r="2" />
            <circle cx="18" cy="6" r="2" />
            <circle cx="6" cy="18" r="2" />
            <circle cx="18" cy="18" r="2" />
            <line x1="7.5" y1="7.5" x2="10.5" y2="10.5" />
            <line x1="16.5" y1="7.5" x2="13.5" y2="10.5" />
            <line x1="7.5" y1="16.5" x2="10.5" y2="13.5" />
            <line x1="16.5" y1="16.5" x2="13.5" y2="13.5" />
          </svg>
        </div>
        <p>Graph will appear after crawling completes.</p>
      </div>
    );
  }

  return (
    <div className="graph-view">
      <div className="panel-header">
        <div className="panel-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="2" />
            <circle cx="6" cy="6" r="2" />
            <circle cx="18" cy="18" r="2" />
            <line x1="7.5" y1="7.5" x2="10.5" y2="10.5" />
            <line x1="13.5" y1="13.5" x2="16.5" y2="16.5" />
          </svg>
        </div>
        <h2>Site Graph</h2>
        <div className="graph-legend">
          <span className="legend-item"><span className="legend-dot safe" /> Clean</span>
          <span className="legend-item"><span className="legend-dot danger" /> Dark Pattern</span>
        </div>
      </div>

      <div className="graph-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="#334155" gap={20} size={1} />
          <Controls
            style={{
              background: '#1e293b',
              borderRadius: '8px',
              border: '1px solid #334155',
            }}
          />
          <MiniMap
            nodeColor={(node) =>
              node.style?.background === '#dc2626' ? '#dc2626' : '#2563eb'
            }
            maskColor="rgba(15, 23, 42, 0.8)"
            style={{
              background: '#1e293b',
              borderRadius: '8px',
              border: '1px solid #334155',
            }}
          />
        </ReactFlow>
      </div>
    </div>
  );
};

export default GraphView;
