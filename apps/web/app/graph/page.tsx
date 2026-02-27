"use client";

import { useEffect, useState, useRef } from "react";
import { apiFetch } from "../../lib/api";

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
  cooperative: "#2d7d46",
  roaster: "#6b4423",
  region: "#2563eb",
  certification: "#d97706",
};

const NODE_LABELS: Record<string, string> = {
  cooperative: "Kooperative",
  roaster: "Rösterei",
  region: "Region",
  certification: "Zertifizierung",
};

const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;

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
  const [panX] = useState(0);
  const [panY] = useState(0);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const animationRef = useRef<number | null>(null);
  const [, forceUpdate] = useState({});  // Trigger re-renders for canvas updates

  // Load network data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch<NetworkData>(`/graph/network?node_types=${nodeFilter}`);
        setNetworkData(data);
        initializePositions(data.nodes);
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : String(e);
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadData();
    loadCommunities();
  }, [nodeFilter]);

  async function loadCommunities() {
    try {
      const data = await apiFetch<Community[]>("/graph/communities");
      setCommunities(data);
    } catch (e) {
      console.error("Failed to load communities:", e);
    }
  }

  async function loadEntityAnalysis(node: GraphNode) {
    try {
      const entityId = node.properties.id || node.id.split("_")[1];
      const entityType = node.node_type;
      const analysis = await apiFetch<EntityAnalysis>(
        `/graph/analysis/${entityType}/${entityId}`
      );
      setSelectedAnalysis(analysis);
    } catch (e) {
      console.error("Failed to load entity analysis:", e);
    }
  }

  function initializePositions(nodes: GraphNode[]) {
    const positions = new Map<string, NodePosition>();

    nodes.forEach((node, idx) => {
      const angle = (idx / nodes.length) * 2 * Math.PI;
      const radius = Math.min(CANVAS_WIDTH, CANVAS_HEIGHT) * 0.3;
      positions.set(node.id, {
        x: CANVAS_WIDTH / 2 + Math.cos(angle) * radius,
        y: CANVAS_HEIGHT / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      });
    });

    nodePositionsRef.current = positions;
    forceUpdate({});  // Trigger re-render
  }

  // Simple force-directed layout simulation
  useEffect(() => {
    if (!networkData || nodePositionsRef.current.size === 0) return;

    let frameCount = 0;
    const maxFrames = 200; // Limit simulation to prevent infinite loop

    const simulate = () => {
      if (frameCount >= maxFrames) {
        // Stop animation after max frames
        return;
      }
      
      const positions = nodePositionsRef.current;
      const alpha = 0.1;
      const repulsionStrength = 5000;
      const attractionStrength = 0.01;
      const centerStrength = 0.01;

      // Apply forces
      networkData.nodes.forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;

        // Center force
        pos.vx += (CANVAS_WIDTH / 2 - pos.x) * centerStrength;
        pos.vy += (CANVAS_HEIGHT / 2 - pos.y) * centerStrength;

        // Repulsion between all nodes
        networkData.nodes.forEach((other) => {
          if (node.id === other.id) return;
          const otherPos = positions.get(other.id);
          if (!otherPos) return;

          const dx = pos.x - otherPos.x;
          const dy = pos.y - otherPos.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsionStrength / (dist * dist);

          pos.vx += (dx / dist) * force;
          pos.vy += (dy / dist) * force;
        });
      });

      // Attraction along edges
      networkData.edges.forEach((edge) => {
        const sourcePos = positions.get(edge.source);
        const targetPos = positions.get(edge.target);
        if (!sourcePos || !targetPos) return;

        const dx = targetPos.x - sourcePos.x;
        const dy = targetPos.y - sourcePos.y;
        const force = attractionStrength;

        sourcePos.vx += dx * force;
        sourcePos.vy += dy * force;
        targetPos.vx -= dx * force;
        targetPos.vy -= dy * force;
      });

      // Update positions
      networkData.nodes.forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;

        pos.x += pos.vx * alpha;
        pos.y += pos.vy * alpha;
        pos.vx *= 0.8; // Damping
        pos.vy *= 0.8;
      });

      forceUpdate({});  // Trigger re-render
      frameCount++;
      animationRef.current = requestAnimationFrame(simulate);
    };

    animationRef.current = requestAnimationFrame(simulate);

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [networkData]); // Only re-run when network data changes

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !networkData) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const positions = nodePositionsRef.current;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    // Apply zoom and pan
    ctx.translate(panX, panY);
    ctx.scale(zoom, zoom);

    // Draw edges
    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = 1;
    networkData.edges.forEach((edge) => {
      const sourcePos = positions.get(edge.source);
      const targetPos = positions.get(edge.target);
      if (!sourcePos || !targetPos) return;

      ctx.beginPath();
      ctx.moveTo(sourcePos.x, sourcePos.y);
      ctx.lineTo(targetPos.x, targetPos.y);
      ctx.stroke();
    });

    // Draw nodes
    networkData.nodes.forEach((node) => {
      const pos = positions.get(node.id);
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
      }

      // Draw label on hover
      if (isHovered || isSelected) {
        ctx.fillStyle = "#1f2937";
        ctx.font = "12px sans-serif";
        ctx.fillText(node.label, pos.x + 10, pos.y - 10);
      }
    });

    ctx.restore();
  }, [networkData, zoom, panX, panY, hoveredNode, selectedNode]);

  // Handle canvas click
  function handleCanvasClick(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!networkData) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - panX) / zoom;
    const y = (e.clientY - rect.top - panY) / zoom;

    const positions = nodePositionsRef.current;

    // Find clicked node
    for (const node of networkData.nodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;

      const dx = x - pos.x;
      const dy = y - pos.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 10) {
        setSelectedNode(node);
        loadEntityAnalysis(node);
        return;
      }
    }

    // Click on empty space - deselect
    setSelectedNode(null);
    setSelectedAnalysis(null);
  }

  // Handle canvas mouse move for hover
  function handleCanvasMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!networkData) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - panX) / zoom;
    const y = (e.clientY - rect.top - panY) / zoom;

    const positions = nodePositionsRef.current;

    // Find hovered node
    for (const node of networkData.nodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;

      const dx = x - pos.x;
      const dy = y - pos.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 10) {
        setHoveredNode(node.id);
        return;
      }
    }

    setHoveredNode(null);
  }

  if (loading) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div className="h1">🕸️ Knowledge Graph</div>
        </div>
        <div className="panel">
          <div className="panelBody">Lädt Netzwerk-Daten...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div className="h1">🕸️ Knowledge Graph</div>
        </div>
        <div className="panel">
          <div className="error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">🕸️ Knowledge Graph</div>
          <div className="muted">
            Beziehungen zwischen Kooperativen, Röstereien, Regionen und Zertifizierungen
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 350px", gap: "1rem" }}>
        {/* Main Graph Canvas */}
        <div className="panel">
          <div className="panelTitle">
            Netzwerk-Visualisierung
            <div className="row gap" style={{ marginLeft: "auto" }}>
              <select
                className="input"
                value={nodeFilter}
                onChange={(e) => setNodeFilter(e.target.value)}
              >
                <option value="all">Alle Knoten</option>
                <option value="cooperative">Nur Kooperativen</option>
                <option value="roaster">Nur Röstereien</option>
                <option value="region">Nur Regionen</option>
                <option value="certification">Nur Zertifizierungen</option>
                <option value="cooperative,region">Kooperativen + Regionen</option>
              </select>
              <button className="btn btn-sm" onClick={() => setZoom(zoom * 1.2)}>
                +
              </button>
              <button className="btn btn-sm" onClick={() => setZoom(zoom / 1.2)}>
                −
              </button>
            </div>
          </div>
          <div className="panelBody" style={{ padding: 0 }}>
            <canvas
              ref={canvasRef}
              width={CANVAS_WIDTH}
              height={CANVAS_HEIGHT}
              onClick={handleCanvasClick}
              onMouseMove={handleCanvasMouseMove}
              style={{ cursor: "pointer", display: "block" }}
            />
          </div>
          <div className="panelFooter">
            <div className="row gap">
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <div key={type} className="row gap" style={{ alignItems: "center" }}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: "50%",
                      backgroundColor: color,
                    }}
                  />
                  <span className="small">{NODE_LABELS[type]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Graph Stats */}
          {networkData && (
            <div className="panel">
              <div className="panelTitle">Graph-Statistiken</div>
              <div className="panelBody">
                <table className="table">
                  <tbody>
                    <tr>
                      <td>Knoten</td>
                      <td className="text-right">{networkData.stats.total_nodes}</td>
                    </tr>
                    <tr>
                      <td>Kanten</td>
                      <td className="text-right">{networkData.stats.total_edges}</td>
                    </tr>
                    <tr>
                      <td>Dichte</td>
                      <td className="text-right">{networkData.stats.density.toFixed(3)}</td>
                    </tr>
                    <tr>
                      <td>Ø Grad</td>
                      <td className="text-right">{networkData.stats.avg_degree.toFixed(2)}</td>
                    </tr>
                  </tbody>
                </table>
                <div style={{ marginTop: "1rem" }}>
                  <div className="small muted">Knoten-Typen:</div>
                  {Object.entries(networkData.stats.node_types).map(([type, count]) => (
                    <div key={type} className="row" style={{ justifyContent: "space-between" }}>
                      <span className="small">{NODE_LABELS[type] || type}</span>
                      <span className="small">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Selected Node Analysis */}
          {selectedNode && selectedAnalysis && (
            <div className="panel">
              <div className="panelTitle">
                {selectedNode.label}
                <button
                  className="btn btn-sm"
                  onClick={() => {
                    setSelectedNode(null);
                    setSelectedAnalysis(null);
                  }}
                  style={{ marginLeft: "auto" }}
                >
                  ✕
                </button>
              </div>
              <div className="panelBody">
                <div className="small muted">{NODE_LABELS[selectedNode.node_type]}</div>

                <div style={{ marginTop: "1rem" }}>
                  <div className="small muted">Graph-Metriken:</div>
                  <table className="table table-sm">
                    <tbody>
                      <tr>
                        <td>Grad</td>
                        <td className="text-right">{selectedAnalysis.degree}</td>
                      </tr>
                      <tr>
                        <td>Degree Centrality</td>
                        <td className="text-right">
                          {selectedAnalysis.degree_centrality.toFixed(3)}
                        </td>
                      </tr>
                      <tr>
                        <td>Betweenness</td>
                        <td className="text-right">
                          {selectedAnalysis.betweenness_centrality.toFixed(3)}
                        </td>
                      </tr>
                      {selectedAnalysis.community_id !== null && (
                        <tr>
                          <td>Community</td>
                          <td className="text-right">#{selectedAnalysis.community_id}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: "1rem" }}>
                  <div className="small muted">
                    Nachbarn ({selectedAnalysis.neighbors.length}):
                  </div>
                  <div style={{ maxHeight: 150, overflowY: "auto" }}>
                    {selectedAnalysis.neighbors.slice(0, 10).map((neighbor) => (
                      <div key={neighbor.id} className="small">
                        {neighbor.label}
                        <span className="muted"> ({NODE_LABELS[neighbor.node_type]})</span>
                      </div>
                    ))}
                    {selectedAnalysis.neighbors.length > 10 && (
                      <div className="small muted">
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
              <div className="panelTitle">Communities ({communities.length})</div>
              <div className="panelBody" style={{ maxHeight: 300, overflowY: "auto" }}>
                {communities.slice(0, 5).map((community) => (
                  <div key={community.community_id} style={{ marginBottom: "1rem" }}>
                    <div className="small">
                      <strong>Community #{community.community_id}</strong>
                      <span className="muted"> ({community.size} Mitglieder)</span>
                    </div>
                    <div className="small muted">
                      Typ: {NODE_LABELS[community.dominant_type] || community.dominant_type}
                    </div>
                    {community.common_attributes.length > 0 && (
                      <div className="small muted">
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
    </div>
  );
}
