"use client";

import { useEffect, useState, useRef } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import { EmptyState } from "../components/EmptyState";
import { ErrorPanel } from "../components/ErrorPanel";

type GraphNode = {
  id: string;
  label: string;
  node_type: string;
  properties: Record<string, unknown>;
};

type GraphEdge = {
  source: string;
  target: string;
  edge_type: string;
  weight: number;
};

type GraphStats = {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  density: number;
  avg_degree: number;
};

type NetworkData = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: GraphStats;
};

type EntityAnalysis = {
  entity_id: string;
  entity_name: string;
  entity_type: string;
  degree: number;
  degree_centrality: number;
  betweenness_centrality: number;
  neighbors: GraphNode[];
  community_id: number | null;
  community_members: GraphNode[];
};

type Community = {
  community_id: number;
  size: number;
  members: GraphNode[];
  dominant_type: string;
  common_attributes: string[];
};

type NodePosition = {
  x: number;
  y: number;
  vx: number;
  vy: number;
};

const NODE_COLORS: Record<string, string> = {
  cooperative:   "#2d7d46",
  roaster:       "#6b4423",
  region:        "#2563eb",
  certification: "#d97706",
};

const NODE_LABELS: Record<string, string> = {
  cooperative:   "Kooperative",
  roaster:       "Rösterei",
  region:        "Region",
  certification: "Zertifizierung",
};

const CANVAS_W = 800;
const CANVAS_H = 600;

export default function GraphPage() {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<EntityAnalysis | null>(null);
  const [nodeFilter, setNodeFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodePositionsRef = useRef<Map<string, NodePosition>>(new Map());
  const [zoom, setZoom] = useState(1);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const animationRef = useRef<number | null>(null);
  const [, forceUpdate] = useState({});

  useEffect(() => {
    const loadData = async () => {
      if (isDemoMode()) { setLoading(false); return; }
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch<NetworkData>(`/graph/network?node_types=${nodeFilter}`);
        setNetworkData(data);
        initializePositions(data.nodes);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    };

    loadData();
    loadCommunities();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeFilter]);

  async function loadCommunities() {
    try {
      const data = await apiFetch<Community[]>("/graph/communities");
      setCommunities(Array.isArray(data) ? data : []);
    } catch { /* silent */ }
  }

  async function loadEntityAnalysis(node: GraphNode) {
    try {
      const entityId = node.properties.id || node.id.split("_")[1];
      const analysis = await apiFetch<EntityAnalysis>(
        `/graph/analysis/${node.node_type}/${entityId}`
      );
      setSelectedAnalysis(analysis);
    } catch { /* silent */ }
  }

  function initializePositions(nodes: GraphNode[]) {
    const positions = new Map<string, NodePosition>();
    nodes.forEach((node, idx) => {
      const angle = (idx / nodes.length) * 2 * Math.PI;
      const radius = Math.min(CANVAS_W, CANVAS_H) * 0.3;
      positions.set(node.id, {
        x: CANVAS_W / 2 + Math.cos(angle) * radius,
        y: CANVAS_H / 2 + Math.sin(angle) * radius,
        vx: 0, vy: 0,
      });
    });
    nodePositionsRef.current = positions;
    forceUpdate({});
  }

  // Force-directed layout (max 200 frames)
  useEffect(() => {
    if (!networkData || nodePositionsRef.current.size === 0) return;
    let frame = 0;

    const simulate = () => {
      if (frame >= 200) return;
      const positions = nodePositionsRef.current;
      const alpha = 0.1;

      networkData.nodes.forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;
        pos.vx += (CANVAS_W / 2 - pos.x) * 0.01;
        pos.vy += (CANVAS_H / 2 - pos.y) * 0.01;

        networkData.nodes.forEach((other) => {
          if (node.id === other.id) return;
          const op = positions.get(other.id);
          if (!op) return;
          const dx = pos.x - op.x, dy = pos.y - op.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const f = 5000 / (dist * dist);
          pos.vx += (dx / dist) * f;
          pos.vy += (dy / dist) * f;
        });
      });

      networkData.edges.forEach((edge) => {
        const sp = positions.get(edge.source), tp = positions.get(edge.target);
        if (!sp || !tp) return;
        const dx = tp.x - sp.x, dy = tp.y - sp.y;
        sp.vx += dx * 0.01; sp.vy += dy * 0.01;
        tp.vx -= dx * 0.01; tp.vy -= dy * 0.01;
      });

      networkData.nodes.forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;
        pos.x += pos.vx * alpha; pos.y += pos.vy * alpha;
        pos.vx *= 0.8; pos.vy *= 0.8;
      });

      forceUpdate({});
      frame++;
      animationRef.current = requestAnimationFrame(simulate);
    };

    animationRef.current = requestAnimationFrame(simulate);
    return () => { if (animationRef.current) cancelAnimationFrame(animationRef.current); };
  }, [networkData]);

  // Canvas draw
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !networkData) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.scale(zoom, zoom);

    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = 1;
    networkData.edges.forEach((edge) => {
      const sp = nodePositionsRef.current.get(edge.source);
      const tp = nodePositionsRef.current.get(edge.target);
      if (!sp || !tp) return;
      ctx.beginPath();
      ctx.moveTo(sp.x, sp.y);
      ctx.lineTo(tp.x, tp.y);
      ctx.stroke();
    });

    networkData.nodes.forEach((node) => {
      const pos = nodePositionsRef.current.get(node.id);
      if (!pos) return;
      const isHovered = hoveredNode === node.id;
      const isSelected = selectedNode?.id === node.id;
      const radius = isHovered || isSelected ? 8 : 6;

      ctx.fillStyle = NODE_COLORS[node.node_type] || "#6b7280";
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fill();

      if (isHovered || isSelected) {
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "#1f2937";
        ctx.font = "12px sans-serif";
        ctx.fillText(node.label, pos.x + 10, pos.y - 10);
      }
    });

    ctx.restore();
  }, [networkData, zoom, hoveredNode, selectedNode]);

  function getNodeAt(e: React.MouseEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas || !networkData) return null;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;
    for (const node of networkData.nodes) {
      const pos = nodePositionsRef.current.get(node.id);
      if (!pos) continue;
      const dx = x - pos.x, dy = y - pos.y;
      if (Math.sqrt(dx * dx + dy * dy) < 10) return node;
    }
    return null;
  }

  function handleCanvasClick(e: React.MouseEvent<HTMLCanvasElement>) {
    const node = getNodeAt(e);
    if (node) { setSelectedNode(node); loadEntityAnalysis(node); }
    else { setSelectedNode(null); setSelectedAnalysis(null); }
  }

  function handleCanvasMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    const node = getNodeAt(e);
    setHoveredNode(node?.id ?? null);
  }

  if (loading) {
    return (
      <div className="page">
        <div className="pageHeader"><div><div className="h1">Knowledge Graph</div></div></div>
        <div className="panel"><div className="panelBody"><div className="muted">Lädt Netzwerk-Daten...</div></div></div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Knowledge Graph</div>
          <div className="muted">
            Beziehungen zwischen Kooperativen, Röstereien, Regionen und Zertifizierungen
          </div>
        </div>
        <div className="pageActions">
          <button className="btn" onClick={() => setZoom((z) => z * 1.2)} title="Zoom in">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
            </svg>
          </button>
          <button className="btn" onClick={() => setZoom((z) => z / 1.2)} title="Zoom out">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              <line x1="8" y1="11" x2="14" y2="11"/>
            </svg>
          </button>
          <select
            className="input"
            value={nodeFilter}
            onChange={(e) => setNodeFilter(e.target.value)}
            style={{ width: "auto" }}
          >
            <option value="all">Alle Knoten</option>
            <option value="cooperative">Nur Kooperativen</option>
            <option value="roaster">Nur Röstereien</option>
            <option value="region">Nur Regionen</option>
            <option value="certification">Nur Zertifizierungen</option>
            <option value="cooperative,region">Kooperativen + Regionen</option>
          </select>
        </div>
      </div>

      {error && <ErrorPanel message={error} onRetry={() => setNodeFilter((f) => f)} />}

      {!error && !networkData && !loading && (
        <EmptyState
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
          }
          title="Kein Graph"
          text="Backend nicht erreichbar oder noch keine Daten im Graph vorhanden."
        />
      )}

      {networkData && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "var(--space-4)" }}>
          {/* Canvas */}
          <div className="panel">
            <div className="panelHeader">
              <div className="panelTitle">Netzwerk-Visualisierung</div>
              <span className="badge">{networkData.stats.total_nodes} Knoten · {networkData.stats.total_edges} Kanten</span>
            </div>
            <div style={{ padding: 0 }}>
              <canvas
                ref={canvasRef}
                width={CANVAS_W}
                height={CANVAS_H}
                onClick={handleCanvasClick}
                onMouseMove={handleCanvasMouseMove}
                style={{ cursor: "pointer", display: "block", width: "100%", maxWidth: CANVAS_W }}
              />
            </div>
            <div style={{ padding: "var(--space-3) var(--space-4)", borderTop: "1px solid var(--color-border)", display: "flex", gap: "var(--space-4)", flexWrap: "wrap" }}>
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <div key={type} style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: color, flexShrink: 0 }} />
                  <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" }}>{NODE_LABELS[type]}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            {/* Statistiken */}
            <div className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Graph-Statistiken</div>
              </div>
              <div className="panelBody">
                <div className="table">
                  <table>
                    <tbody>
                      <tr><td>Knoten</td><td style={{ textAlign: "right" }}>{networkData.stats.total_nodes}</td></tr>
                      <tr><td>Kanten</td><td style={{ textAlign: "right" }}>{networkData.stats.total_edges}</td></tr>
                      <tr><td>Dichte</td><td style={{ textAlign: "right" }}>{networkData.stats.density.toFixed(3)}</td></tr>
                      <tr><td>Ø Grad</td><td style={{ textAlign: "right" }}>{networkData.stats.avg_degree.toFixed(2)}</td></tr>
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: "var(--space-4)" }}>
                  <div className="fieldLabel">Knoten-Typen</div>
                  {Object.entries(networkData.stats.node_types).map(([type, count]) => (
                    <div key={type} style={{ display: "flex", justifyContent: "space-between", marginTop: "var(--space-1)" }}>
                      <span style={{ fontSize: "var(--font-size-sm)" }}>{NODE_LABELS[type] || type}</span>
                      <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Selektierter Knoten */}
            {selectedNode && selectedAnalysis && (
              <div className="panel">
                <div className="panelHeader">
                  <div className="panelTitle">{selectedNode.label}</div>
                  <button
                    className="btn"
                    onClick={() => { setSelectedNode(null); setSelectedAnalysis(null); }}
                    style={{ padding: "2px 8px", fontSize: "var(--font-size-xs)" }}
                  >
                    Schliessen
                  </button>
                </div>
                <div className="panelBody">
                  <div className="muted" style={{ marginBottom: "var(--space-3)" }}>
                    {NODE_LABELS[selectedNode.node_type]}
                  </div>
                  <div className="table">
                    <table>
                      <tbody>
                        <tr><td>Grad</td><td style={{ textAlign: "right" }}>{selectedAnalysis.degree}</td></tr>
                        <tr><td>Degree Centrality</td><td style={{ textAlign: "right" }}>{selectedAnalysis.degree_centrality.toFixed(3)}</td></tr>
                        <tr><td>Betweenness</td><td style={{ textAlign: "right" }}>{selectedAnalysis.betweenness_centrality.toFixed(3)}</td></tr>
                        {selectedAnalysis.community_id !== null && (
                          <tr><td>Community</td><td style={{ textAlign: "right" }}>#{selectedAnalysis.community_id}</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div style={{ marginTop: "var(--space-3)" }}>
                    <div className="fieldLabel">Nachbarn ({selectedAnalysis.neighbors.length})</div>
                    <div style={{ maxHeight: 150, overflowY: "auto", marginTop: "var(--space-2)" }}>
                      {selectedAnalysis.neighbors.slice(0, 10).map((n) => (
                        <div key={n.id} style={{ fontSize: "var(--font-size-sm)", padding: "2px 0" }}>
                          {n.label}
                          <span className="muted"> ({NODE_LABELS[n.node_type]})</span>
                        </div>
                      ))}
                      {selectedAnalysis.neighbors.length > 10 && (
                        <div className="muted" style={{ fontSize: "var(--font-size-xs)" }}>
                          ... und {selectedAnalysis.neighbors.length - 10} weitere
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Communities */}
            {communities.length > 0 && (
              <div className="panel">
                <div className="panelHeader">
                  <div className="panelTitle">Communities</div>
                  <span className="badge">{communities.length}</span>
                </div>
                <div className="panelBody" style={{ maxHeight: 280, overflowY: "auto" }}>
                  {communities.slice(0, 5).map((community) => (
                    <div key={community.community_id} style={{ marginBottom: "var(--space-4)" }}>
                      <div style={{ fontWeight: "var(--font-weight-semibold)", fontSize: "var(--font-size-sm)" }}>
                        Community #{community.community_id}
                        <span className="muted"> ({community.size} Mitglieder)</span>
                      </div>
                      <div className="muted" style={{ fontSize: "var(--font-size-xs)", marginTop: 2 }}>
                        Typ: {NODE_LABELS[community.dominant_type] || community.dominant_type}
                      </div>
                      {community.common_attributes.length > 0 && (
                        <div className="muted" style={{ fontSize: "var(--font-size-xs)" }}>
                          Attribute: {community.common_attributes.slice(0, 3).join(", ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
